from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import re
import fitz 
import logging
_logger = logging.getLogger(__name__)

style_css_custom = {
    'green':""" background-color: green;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #fff;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;""",
    'gray':""" background-color: gray;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #000;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;""",
    'red':""" background-color: red;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #fff;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;""",
}



class AccountMove(models.Model):
    _inherit= 'account.move'
    acuse_state_badge = fields.Html(string="Acuse de recibo", compute='_compute_acuse_state_badge', readonly=True)
    reclamo_state_badge = fields.Html(string="Reclamo de la Factura", compute='_compute_reclamo_state_badge', readonly=True)
    recibo_state_badge = fields.Html(string="Recibo del bien y/o servicio", compute='_compute_recibo_state_badge', readonly=True)
    tacita_state_badge = fields.Html(string="Aceptación Tácita", compute='_compute_tacita_state_badge', readonly=True)
    expresa_state_badge = fields.Html(string="Aceptación expresa", compute='_compute_expresa_state_badge', readonly=True)
    acuse_block = fields.Boolean(string="Estado Acuse en la DIAN OK",default=False)
    reclamo_block = fields.Boolean(string="Estado Reclamo en la DIAN OK",default=False)
    recibo_block = fields.Boolean(string="Estado Recibido en la DIAN OK",default=False)
    tacita_block = fields.Boolean(string="Estado Tacita en la DIAN OK",default=False)
    expresa_block = fields.Boolean(string="Estado Expresa en la DIAN OK",default=False)
    acuse_rechazo = fields.Boolean(string="Estado Acuse en la DIAN OK")
    reclamo_rechazo = fields.Boolean(string="Estado Reclamo en la DIAN OK")
    recibo_rechazo = fields.Boolean(string="Estado Recibido en la DIAN OK")
    tacita_rechazo = fields.Boolean(string="Estado Tacita en la DIAN OK")
    expresa_rechazo = fields.Boolean(string="Estado Expresa en la DIAN OK")


    exp_invoice_file = fields.Binary(string='Factura proveedor')
    original_filename = fields.Char(string='Nombre Original del Archivo')
    acuse_recibo_id = fields.Many2many('acuse.recibo',string='Acuse recibo')
    acuse_journal_id = fields.Many2one('account.journal', string="Diario")
    set_acuse_recibo_ok = fields.Boolean(string='Acuse configurado',default=False)
    set_acuse_values_ok = fields.Boolean(string='Acuse con valores',default=False)
    send_acuse_dian_ok = fields.Boolean(string='Acuse enviado',default=False)
    invoice_cufe = fields.Char(string="CUFE")
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



    @api.depends('acuse_block')
    def _compute_acuse_state_badge(self):
        for record in self:
            style = ''
            text = ''
            if record.acuse_block == True :
                style = style_css_custom['green']
                text = 'Aceptado'
            else:
                if record.acuse_rechazo == False:
                    style = style_css_custom['gray']
                    text = 'Pendiente'  
                else:
                    style = style_css_custom['red']
                    text = 'Rechazado'  
            record.acuse_state_badge = f"""
                <div style="width: 100px; text-align: center; {style} color: white;">
                    <span style="display: block;">{text}</span>
                </div>
            """

    @api.depends('reclamo_block')
    def _compute_reclamo_state_badge(self):
        for record in self:
            style = ''
            text = ''
            if record.reclamo_block == True :
                style = style_css_custom['green']
                text = 'Aceptado'
            else:
                if record.reclamo_rechazo == False:
                    style = style_css_custom['gray']
                    text = 'Pendiente'  
                else:
                    style = style_css_custom['red']
                    text = 'Rechazado'         
            record.reclamo_state_badge = f"""
                <div style="width: 100px; text-align: center; {style} color: white;">
                    <span style="display: block;">{text}</span>
                </div>
            """

    @api.depends('recibo_block')
    def _compute_recibo_state_badge(self):
        for record in self:
            style = ''
            text = ''
            if record.recibo_block == True :
                style = style_css_custom['green']
                text = 'Aceptado'
            else:
                if record.recibo_rechazo == False:
                    style = style_css_custom['gray']
                    text = 'Pendiente'  
                else:
                    style = style_css_custom['red']
                    text = 'Rechazado'           
            record.recibo_state_badge = f"""
                <div style="width: 100px; text-align: center; {style} color: white;">
                    <span style="display: block;">{text}</span>
                </div>
            """

    @api.depends('tacita_block')
    def _compute_tacita_state_badge(self):
        for record in self:
            style = ''
            text = ''
            if record.tacita_block == True :
                style = style_css_custom['green']
                text = 'Aceptado'
            else:
                if record.tacita_rechazo == False:
                    style = style_css_custom['gray']
                    text = 'Pendiente'  
                else:
                    style = style_css_custom['red']
                    text = 'Rechazado'           
            record.tacita_state_badge = f"""
                <div style="width: 100px; text-align: center; {style} color: white;">
                    <span style="display: block;">{text}</span>
                </div>
            """

    @api.depends('expresa_block')
    def _compute_expresa_state_badge(self):
        for record in self:
            style = ''
            text = ''
            if record.expresa_block == True :
                style = style_css_custom['green']
                text = 'Aceptado'
            else:
                if record.expresa_rechazo == False:
                    style = style_css_custom['gray']
                    text = 'Pendiente'  
                else:
                    style = style_css_custom['red']
                    text = 'Rechazado'            
            record.expresa_state_badge = f"""
                <div style="width: 100px; text-align: center; {style} color: white;">
                    <span style="display: block;">{text}</span>
                </div>
            """

    @api.onchange('exp_invoice_file')
    def _onchange_binary_file(self):
        if self.exp_invoice_file and self.original_filename:            
            self.exp_invoice_file = self.exp_invoice_file.decode('utf-8')

    # 1
    def set_acuse_recibo(self):
        for acuse in self.acuse_recibo_id:
            if acuse.tipo_evento_radian == self.tipo_evento_radian and acuse.unlink_bool:
                raise UserError(f'El evento {acuse.tipo_evento_radian} ya fue enviado y aceptado por la DIAN')

        # validaciones
        # if not self.exp_invoice_file:
        #     raise UserError('No ha seleccionado ninguna factura para el Acuse recibido')

        #-------------------------------------------------------------------------------------
        #-----------------CODIGO INGRESADO POR BRAWIL-----------------------------------------
        
        if not self.invoice_cufe and not self.exp_invoice_file:
            raise UserError("Debe ingresar el CUFE de la factura o subir el archivo XML/PDF.")
        if not self.exp_invoice_file and not self.invoice_cufe:
            raise UserError("Debe ingresar el CUFE de la factura en el campo correspondiente.")

        if not self or not self.ref:
            raise UserError("Debe ingresar la referencia de la factura proveedor.")

        #-------------------------------------------------------------------------------------
        #-----------------CODIGO INGRESADO POR BRAWIL-----------------------------------------
        
        if not self.acuse_journal_id:
            raise UserError('No ha seleccionado ningun Diaro para enviar el Acuse')

        if self.tipo_evento_radian in ['031'] and not self.tipo_de_rechazo_reclamo:
            raise UserError('Debe seleccionar el tipo de Reclamo')

        # pdf_data = base64.b64decode(self.exp_invoice_file)
        # # Utiliza PyMuPDF para extraer texto del PDF
        # pdf_document = fitz.open(stream=pdf_data, filetype='pdf')
        # pdf_text = ''

        # for page_num in range(len(pdf_document)):
        #     page = pdf_document[page_num]
        #     pdf_text += page.get_text()

        # # Expresión regular para buscar un hexadecimal de 64 o más caracteres
        # hex_pattern = r'[0-9a-fA-F]{96}'

        # # Buscar la expresión regular en el texto extraído
        # cufe_cude = re.findall(hex_pattern, pdf_text)

        # if not cufe_cude:
        #     raise UserError("EL pdf de la factura no tiene CUFE")

        cufe_cude = []
        
        # 1. Si se subió el archivo PDF, intenta extraer el CUFE de allí
        if self.exp_invoice_file:
            try:
                pdf_data = base64.b64decode(self.exp_invoice_file)
                pdf_document = fitz.open(stream=pdf_data, filetype='pdf')
                pdf_text = ''
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    pdf_text += page.get_text()
        
                # Buscar CUFE en el PDF
                # Nota: Algunas veces el CUFE tiene 96 o 97 caracteres hexadecimales
                hex_pattern = r'[0-9a-fA-F]{95,100}'
                cufe_cude = re.findall(hex_pattern, pdf_text)
        
                if cufe_cude:
                    # Tomar el primero encontrado
                    self.invoice_cufe = cufe_cude[0]
                    _logger.info(f"CUFE extraído del PDF: {cufe_cude[0]}")
                else:
                    _logger.warning("No se encontró CUFE en el PDF cargado.")
        
            except Exception as e:
                raise UserError(f"No se pudo procesar el PDF de la factura. Error: {str(e)}")
        
        # 2. Si no se extrajo del PDF pero el usuario lo digitó, usar ese
        if not cufe_cude and self.invoice_cufe:
            cufe_cude = [self.invoice_cufe]
        
        # 3. Validación final
        if not cufe_cude:
            raise UserError("Debe subir una factura PDF válida con CUFE o ingresar el CUFE manualmente.")



        acuse_data = {
            'invoice': self.id,
            'cufe_cude': cufe_cude[0],
            'company_id': self.company_id.id,
            'xml_filename': 'a.xml',
            'zipped_filename': 'b.zip',            
            'journal_id' : self.acuse_journal_id.id,
            'tipo_documento' : self.tipo_documento,
            'tipo_evento_radian' : self.tipo_evento_radian,
            'tipo_de_rechazo_reclamo':self.tipo_de_rechazo_reclamo,

        }
        self.update({'invoice_cufe':cufe_cude[0]})
        acuse_create = self.env['acuse.recibo'].create(acuse_data)


        self.write({
            'acuse_recibo_id': [(4,acuse_create.id)]
        })

        self.update({'set_acuse_recibo_ok':True})
        self.update({'set_acuse_values_ok':True})
        self.update({'send_acuse_dian_ok':False})

    # 2
    def set_acuse_values(self):
        for acuse in self.acuse_recibo_id:
            if acuse.tipo_evento_radian == self.tipo_evento_radian and acuse.unlink_bool == False:
                res = acuse.get_status()
                if res:
                    self.update({'set_acuse_recibo_ok':True})
                    self.update({'set_acuse_values_ok':False})
                    self.update({'send_acuse_dian_ok':True})
                else:
                    self.update_send_to_start()


    # 3
    def send_acuse_dian(self):
        for acuse in self.acuse_recibo_id:
            if acuse.tipo_evento_radian == self.tipo_evento_radian and acuse.unlink_bool == False:
                res = acuse.action_send_acuse()
                if res == True:
                    self.update({'set_acuse_recibo_ok':False})
                    self.update({'set_acuse_values_ok':False})
                    self.update({'send_acuse_dian_ok':False})

                    if acuse.tipo_evento_radian == '030':
                        self.update({'acuse_block':True})
                    if acuse.tipo_evento_radian == '031':
                        self.update({'reclamo_block':True})
                    if acuse.tipo_evento_radian == '032':
                        self.update({'recibo_block':True})
                    if acuse.tipo_evento_radian == '033':
                        self.update({'tacita_block':True})
                    if acuse.tipo_evento_radian == '034':
                        self.update({'expresa_block':True})

                else:
                    self.update_send_to_start()

                    if acuse.tipo_evento_radian == '030':
                        self.update({'acuse_rechazo':True})
                    if acuse.tipo_evento_radian == '031':
                        self.update({'reclamo_rechazo':True})
                    if acuse.tipo_evento_radian == '032':
                        self.update({'recibo_rechazo':True})
                    if acuse.tipo_evento_radian == '033':
                        self.update({'tacita_rechazo':True})
                    if acuse.tipo_evento_radian == '034':
                        self.update({'expresa_rechazo':True})

    def update_send_to_start(self):
        self.update({'set_acuse_recibo_ok':False})
        self.update({'set_acuse_values_ok':False})
        self.update({'send_acuse_dian_ok':False})

        for acuse in self.acuse_recibo_id:
            if acuse.tipo_evento_radian == self.tipo_evento_radian and acuse.unlink_bool == False:
                self.update({'acuse_recibo_id':[(3, acuse.id)]})

        return True
