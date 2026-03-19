from odoo import fields, models, api, _
import json

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    tipo_planeacion = fields.Selection(
        selection=[('automatico','automatico'),('semiautomatico','semiautomatico')],
        string='Tipo de Planeación',
    )
    dominio = fields.Char()
    oleada_pos = fields.Boolean(string = "Oleadas en PTV")
    piso = fields.Boolean(string = "piso")
    pasillo = fields.Boolean(string = "pasillo")
    turbo = fields.Boolean(string = "turbo")
    clk = fields.Boolean(string = "clk")
    mkp = fields.Boolean(string = "mkp")
    flex = fields.Boolean(string = "flex")


    def planear_automatico(self):
        for record in self:
            if record.tipo_planeacion == 'automatico':
                if record.dominio:
                    datos = json.loads(record.dominio)
                else:
                    datos = {'almacen':record.id}
                registro = self.env['filter.order'].create(datos)
                registro.planear()