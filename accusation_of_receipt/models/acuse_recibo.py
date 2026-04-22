from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import base64
from io import BytesIO
from . import global_functions
from datetime import date
from requests import post, exceptions
from lxml import etree
from pytz import timezone
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from zipfile import ZipFile
import logging
_logger = logging.getLogger(__name__)

DIAN = {'wsdl-hab': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
        'wsdl': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc'}


class AcuseRecibo(models.Model):
    _name= 'acuse.recibo'

    unlink_bool = fields.Boolean(string="Estado Aceptado en la DIAN",default=False)
    name = fields.Char(string="Acuse")
    invoice = fields.Many2one('account.move', string="Factura")
    cufe_cude = fields.Char(string='CUFE/CUDE', tracking=True)
    send_cufe_cude = fields.Char(string='CUFE/CUDE Enviado', tracking=True)
    uncoded_send_cufe_cude = fields.Char(string='CUFE/CUDE Enviado dec', tracking=True)
    company_id = fields.Many2one('res.company', string='Company')
    exp_accepted_file = fields.Binary(string='Explicit Accepted File')
    xml_filename = fields.Char(string='XML Filename')
    zipped_filename = fields.Char(string='Zipped Filename')
    dian_response_text = fields.Text(string="Respuesta DIAN")

    tipo_documento = fields.Selection([
        ('01', 'Factura electrónica de venta'),
        ('03', 'Instrumento electrónico de transmisión – tipo 03'),
        ('04', 'Factura electrónica de Venta ‐ tipo 04'),
        ('91', 'Nota Crédito'),
        ('92', 'Nota Débito'),
        ('96', 'Eventos (AplicationResponse)')
    ], string='Tipo de Documento',default='01')

    tipo_evento_radian = fields.Selection([
        ('030', 'Acuse de recibo de Factura Electrónica de Venta'),
        ('031', 'Reclamo de la Factura Electrónica de Venta'),
        ('032', 'Recibo del bien y/o prestación del servicio'),
        ('033', 'Aceptación Tácita'),
        ('034', 'Aceptación expresa')
    ], string='Tipo de Evento RADIAN',default='030')

    tipo_de_rechazo_reclamo = fields.Selection([
        ('1', 'Documento con inconsistencias'),
        ('2', 'Mercancía no entregada totalmente'),
        ('3', 'Mercancía no entregada parcialmente'),
        ('4', 'Servicio no prestado')
    ], string='Tipo de Reclamo')

    journal_id = fields.Many2one('account.journal',string="Secuencia")


    def unlink(self):
        for record in self:
            if record.unlink_bool == True:
                raise UserError("No se permite la eliminación de este registro la DIAN ya acepto este Evento.")
        return super(AcuseRecibo, self).unlink()

    def write(self,vals):
        for record in self:
            if record.unlink_bool == True:
                raise UserError("No se permite la modificacion de este registro la DIAN ya acepto este Evento.")
        return super(AcuseRecibo, self).write(vals)

    def _get_GetStatus_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['trackId'] = self.cufe_cude
        return xml_soap_values
    
    def get_status(self):
        self._set_filenames()
        xml_with_signature = self.get_provider_invoice_values()
        self.write({'exp_accepted_file': b64encode(self._get_acp_zipped_file(xml_with_signature)).decode("utf-8", "ignore")})
        return True

    def _get_acp_zipped_file(self, file):
        output = BytesIO()
        zipfile = ZipFile(output, mode='w')
        zipfile_content = BytesIO()
        # zipfile_content.write(b64decode(file))
        zipfile_content.write(file)
        zipfile.writestr(self.xml_filename, zipfile_content.getvalue())
        # zipfile.writestr(self.xml_filename,file)
        zipfile.close()
        return output.getvalue()

    def get_sequence_and_prefix(self):
        prefix = self.journal_id.sequence_id.prefix
        if self.journal_id.sequence_number_next == 1:
            number = self.journal_id.sequence_number_next
            self.journal_id.update({'sequence_number_next':self.journal_id.sequence_number_next + 1})
        else:
            self.journal_id.update({'sequence_number_next':self.journal_id.sequence_number_next + 1})
            number = self.journal_id.sequence_number_next

        return {'prefix':prefix,'number':number}

    def get_provider_invoice_values(self):
        Event_Values = {}
        Event_Values['ei_software_id'] = self.company_id.software_id
        sequence = self.get_sequence_and_prefix()
        # ID = self.invoice.name
        ID =  f"{sequence['prefix']}{sequence['number']}"
        self.update({'name':ID})

        software_security_code = global_functions.get_software_security_code(
            Event_Values['ei_software_id'] ,
            self.company_id.software_pin,
            ID)
        Event_Values['software_security_code'] = software_security_code['SoftwareSecurityCode']
        document_number = self.company_id.partner_id.identification_document
        Event_Values['document_number'] = document_number
        Event_Values['check_digit'] = self.company_id.partner_id.check_digit
        Event_Values['profile_execution_id'] = self.company_id.profile_execution_id
        Event_Values['application_response_id'] = ID
        date_format = str(datetime.now())[0:19]        
        create_date = datetime.strptime(date_format, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        de_issue_date = date.today()
        de_issue_time = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')
        Event_Values['de_issue_date'] = de_issue_date
        Event_Values['de_issue_time'] = de_issue_time
        Event_Values['invoice_customer_party_name'] = self.company_id.name   
        Event_Values['invoice_customer_identification_digit'] = self.company_id.partner_id.check_digit
        Event_Values['invoice_customer_identification'] = self.company_id.partner_id.identification_document
        Event_Values['invoice_customer_document_type'] = self.company_id.partner_id.document_type_id.code       
        Event_Values['invoice_customer_type_person'] = self.company_id.partner_id.person_type
        #revisar este valor que viene desde la posicion fiscla del res.partner
        Event_Values['invoice_customer_responsabilidad_tributaria'] = self.company_id.partner_id.property_account_position_id.tax_scheme_id.code
        Event_Values['invoice_customer_responsabilidad_tributaria_text'] = self.company_id.partner_id.property_account_position_id.tax_scheme_id.name

        Event_Values['invoice_supplier_party_name'] = self.invoice.partner_id.name
        Event_Values['invoice_supplier_identification_digit'] = self.invoice.partner_id.check_digit
        Event_Values['invoice_supplier_type_person'] = self.invoice.partner_id.person_type
        Event_Values['invoice_supplier_identification'] = self.invoice.partner_id.identification_document
        Event_Values['invoice_supplier_responsabilidad_tributaria'] = self.invoice.partner_id.property_account_position_id.tax_scheme_id.code
        Event_Values['invoice_supplier_responsabilidad_tributaria_text'] = self.invoice.partner_id.property_account_position_id.tax_scheme_id.name
        # es el mismo campo de la factrua revisar si se deben quitar caracteres especiales como /
        Event_Values['document_reference'] = self.invoice.ref.replace(" ","")
        # confirmar si el document_type_reference se puede sacar de la factura
        Event_Values['profile_execution_cude_id'] = self.company_id.profile_execution_id
        # Event_Values['document_type_reference'] = self.tipo_documento
        Event_Values['document_type_reference'] = self.tipo_documento
        # estos datos deben venir del proveedor desde la factura.
        Event_Values['receiver_document_type'] = self.company_id.partner_id.document_type_id.code
        Event_Values['receiver_id'] = self.company_id.partner_id.identification_document
        Event_Values['receiver_verification_digit'] = self.company_id.partner_id.check_digit    
        usuario = self.env['res.users'].browse(self.env.uid)
        # Acceder a la información del usuario
        nombre_usuario = f"{usuario.firstname} {usuario.othernames}"
        apellido_usuario = f"{usuario.lastname} {usuario.lastname2}"
        _logger.info(str([nombre_usuario,apellido_usuario]))

        if usuario.firstname and apellido_usuario:
            Event_Values['receiver_first_name'] = f"{usuario.firstname} {usuario.othernames or ''}"
            Event_Values['receiver_second_name'] = f"{usuario.lastname} {usuario.lastname2 or ''}"
        else:
            Event_Values['receiver_first_name'] = usuario.name
            Event_Values['receiver_second_name'] = usuario.name

        Event_Values['receiver_job_title'] = usuario.partner_id.function or ""
        concepto_rechazo = ''
        codigo_rechazo = ''
        if self.tipo_de_rechazo_reclamo in ['1']:
            concepto_rechazo = 'Documento con inconsistencias'
            codigo_rechazo = '01'
        if self.tipo_de_rechazo_reclamo in ['2']:
            concepto_rechazo = 'Mercancía no entregada totalmente'
            codigo_rechazo = '02'
        if self.tipo_de_rechazo_reclamo in ['3']:
            concepto_rechazo = 'Mercancía no entregada parcialmente'
            codigo_rechazo = '03'
        if self.tipo_de_rechazo_reclamo in ['4']:
            concepto_rechazo = 'Servicio no prestado'
            codigo_rechazo = '04'

        Event_Values['concepto_del_rechazo'] = concepto_rechazo
        Event_Values['codigo_concepto_del_rechazo'] = codigo_rechazo


        de_cude = global_functions.get_cufe_cude_de(
            Num_DE=str(ID or ''),
            Fec_Emi=str(de_issue_date or ''),
            Hor_Emi=str(de_issue_time or ''),
            NitFE=str(self.company_id.partner_id.identification_document or ''),
            DocAdq=str(self.invoice.partner_id.identification_document or ''),
            ResponseCode=str(self.tipo_evento_radian or ''),
            ID_D=str(self.invoice.ref or '').replace(" ", ""),
            DocumentTypeCode=str(self.tipo_documento or ''),
            SoftwarePIN=str(self.company_id.software_pin or '')
)

        self.write({'send_cufe_cude':de_cude['CUFE/CUDE'],'uncoded_send_cufe_cude':de_cude['CUFE/CUDEUncoded']})
        # EL CUFE REAL ES self.cufe_cuede DE LA FACTURA O DOCUMENTO ELECTRONICO
        Event_Values['invoice_cufe'] = self.cufe_cude
        Event_Values['de_cude'] = de_cude['CUFE/CUDE']

        if self.tipo_evento_radian == '030':
            template_to_send = global_functions.get_template_xml(Event_Values, 'Acuse')
        elif self.tipo_evento_radian == '031':
            template_to_send = global_functions.get_template_xml(Event_Values, 'Reclamo')
        elif self.tipo_evento_radian == '032':
            template_to_send = global_functions.get_template_xml(Event_Values, 'Recibo_B')
        elif self.tipo_evento_radian == '033':
            template_to_send = global_functions.get_template_xml(Event_Values, 'Aceptacion_Tacita')
        elif self.tipo_evento_radian == '034':
            template_to_send = global_functions.get_template_xml(Event_Values, 'Aceptacion_Expresa')
        else:
            raise UserError("No selecciono ningun tipo de evento RADIAN")

        xml_with_signature = global_functions.get_xml_with_signature(
            template_to_send,
            self.company_id.signature_policy_url, 
            self.company_id.signature_policy_description, 
            self.company_id.certificate_file, 
            self.company_id.certificate_password)

        return xml_with_signature

    def action_send_acuse(self):
        # URL de conexion en ambiente de pruebas
        # wsdl = 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl'
        wsdl = DIAN['wsdl-hab']
        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']
        
        Event_Values = self._get_AcceptedSendBillAsync_values(self.exp_accepted_file)
        Event_Values['To'] = wsdl
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(Event_Values, 'SendEventUpdateStatus'),            
            Event_Values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding="unicode"))        

        if response.status_code == 200:
            res = self._get_status_response(response,False)
            if res == True:
                return True
            else:
                return res
            
        else:
            return response.status_code            

    def _get_status_response(self, response, send_mail):
        b = "http://schemas.datacontract.org/2004/07/DianResponse"
        root = etree.fromstring(response.content)

        for element in root.iter("{%s}StatusCode" % b):
            for element_int in root.iter("{%s}IsValid" % b):
                if element.text == '00' or element_int.text == 'true':
                    self.update({'dian_response_text':'Aceptado por la DIAN'})
                    self.update({'unlink_bool':True})
                    return True
        else:
            content = etree.fromstring(response.text)
            content_string = etree.tostring(content, pretty_print=True).decode()
            self.update({'dian_response_text':content_string})
            return content_string

    def _get_AcceptedSendBillAsync_values(self, accepted_file):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = accepted_file.decode("utf-8", "ignore")
        # xml_soap_values['contentFile'] = accepted_file
        return xml_soap_values

    def _set_filenames(self):
        #nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos
        # alineados a la derecha y relleno con ceros a la izquierda.
        if self.company_id.partner_id.identification_document:
            nnnnnnnnnn = self.company_id.partner_id.identification_document.zfill(10)
        else:
            raise ValidationError("The company identification document is not "
                                  "established in the partner.\n\nGo to Contacts > "
                                  "[Your company name] to configure it.")
        #El Código “ppp” es 000 para Software Propio
        ppp = '000'
        #aa: Dos (2) últimos dígitos año calendario
        aa = datetime.now().replace(
            tzinfo=timezone('America/Bogota')).strftime('%y')
        #dddddddd: consecutivo del paquete de archivos comprimidos enviados;
        # de ocho (8) dígitos decimales alineados a la derecha y ajustado a la
        # izquierda con ceros; en el rango:
        #   00000001 <= 99999999
        # Ejemplo de la décima primera factura del Facturador Electrónico con
        # NIT 901138658 con software propio para el año 2019.
        # Regla: el consecutivo se iniciará en “00000001” cada primero de enero.
        out_invoice_sent = self.company_id.out_invoice_sent
        out_refund_sent = self.company_id.out_refund_sent
        in_refund_sent = self.company_id.in_refund_sent
        zip_sent = out_invoice_sent + out_refund_sent + in_refund_sent
        xml_filename_prefix = 'ar'

        dddddddd = str(hex(self.journal_id.sequence_number_next).split("x")[1]).zfill(8)
        zdddddddd = str(hex(self.journal_id.sequence_number_next + zip_sent).split("x")[1]).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + dddddddd
        znnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + zdddddddd

        self.write({
            'xml_filename': xml_filename_prefix + nnnnnnnnnnpppaadddddddd + '.xml',
            'zipped_filename': 'z' + znnnnnnnnnnpppaadddddddd + '.zip'})
