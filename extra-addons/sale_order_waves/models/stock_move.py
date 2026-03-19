from odoo import fields, models, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    reportar_error = fields.Selection(string="Reportar Error", selection=[('sobrante', 'Sobrante'),
                                                                          ('faltante', 'Faltante'),
                                                                          ('trocado', 'Trocado')])

    encargado_picking = fields.Many2one('res.users', string="Responsable picking", compute="compute_responsable")

    def compute_responsable(self):
        for record in self:
            record.encargado_picking = False
            picking = record.picking_id
            try:
                record.encargado_picking = picking.sale_id.picking_ids.filtered(
                    lambda p: 'PICK' in p.name).move_ids_without_package.filtered(
                    lambda s: s.product_id == record.product_id).picking_id.batch_id.user_id.id
            except:
                pass