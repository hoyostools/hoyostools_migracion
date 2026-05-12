from odoo import fields, api, models

class logistic_service_fields(models.Model):
    _inherit = 'sale.order'

    idOrden = fields.Char(string="Id de orden")
    idb4b = fields.Char(string="Id b4b")
    servicio_logistico = fields.Boolean(string="Servicio logistico")
    nombre_logistico = fields.Char(string="Nombre logistico")
    identificacion_logistico = fields.Char(string="Id logistico")
    tipo_id_logistico = fields.Char(string="Cédula/Nit logistico")
    address_logistica = fields.Char(string="Dirección logistico")
    city_logistica = fields.Char(string="Ciudad logistica")
    state_logistico = fields.Char(string="Departamento logistico")
    phone_logistico = fields.Char(string="Telefono logistico")
    guia_url = fields.Char(string='Guía', widget='url')
    fecha_sube = fields.Date(
        string='Fecha Sube',
        widget='date')
    
    transportadora = fields.Char(string='Transportadora')
    notas_logisticas = fields.Char(string="Notas logisticas")