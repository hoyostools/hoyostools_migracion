from odoo import fields, models, api, _

class WaveZonas(models.Model):
    _name = 'wave.zonas'

    name = fields.Char(string='Descripción', default=False)
    ocupado = fields.Boolean(string="Ocupado")
    nombre = fields.Char(string="Nombre")
    metodo_de_envio = fields.Many2one('delivery.carrier', string='Método de Envio', default=False)
    orden = fields.Many2one('sale.order', string='orden', default=False)

    @api.constrains('ocupado')
    def onchange_ocupado(self):
        for record in self:
            if record.ocupado == False:
                record.orden = False
            if not record.orden.procesada:
                record.orden = False