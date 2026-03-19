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
            if 'qty_done' in vals:
                if vals['qty_done'] > 0 and not record.fecha_inicio:
                    vals['fecha_inicio'] = fields.datetime.today()
            if 'date_done' in vals:
                vals['tiempo_tarea'] = (record.fecha_inicio - vals['date_done']) if record.fecha_inicio else 0
        return super(StockMoveLine, self).write(vals)