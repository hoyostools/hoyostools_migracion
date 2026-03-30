from odoo import fields, models, api, _

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    reportar_error = fields.Selection(string="Reportar Error", selection=[('sobrante', 'Sobrante'),
                                                                          ('faltante', 'Faltante'),
                                                                          ('trocado', 'Trocado')])
    encargado_picking = fields.Many2one('res.users', string="Responsable picking", compute="compute_responsable")
    fecha_inicio = fields.Date(string='Fecha inicio ejecución de linea')
    tiempo_tarea = fields.Float(string='tiempo tarea', default = 0.0)

    def compute_responsable(self):
        for record in self:
            record.encargado_picking = False
            picking = record.move_id.picking_id
            try:
                record.encargado_picking = picking.sale_id.picking_ids.filtered(
                    lambda p: 'PICK' in p.name).move_ids_without_package.filtered(
                    lambda s: s.product_id == record.move_id.product_id).picking_id.batch_id.user_id.id
            except:
                pass

    def write(self, vals):
        for record in self:
            if 'picked' in vals:
                if vals['picked'] == True and record.create_date:
                    delta = fields.Datetime.now() - record.create_date
                    tiempo_horas = delta.total_seconds() / 3600
                    vals['tiempo_tarea'] = tiempo_horas

        return super(StockMoveLine, self).write(vals)