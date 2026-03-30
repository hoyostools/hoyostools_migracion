from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    mostrar = fields.Boolean(compute='compute_mostrar')
    ordenes = fields.Many2many('sale.order', string="Ordenes")
    numero_ordenes = fields.Integer(string='Número de Órdenes', store=True, readonly=False, index=True)
    numero_ordenes_real = fields.Integer(string='Número de Órdenes Real', store=True, readonly=False, index=True)
    cantidad_items = fields.Integer(string='Cantidad de Items', store=True, readonly=False, index=True)

    def actualizar_campos_ordenes(self):
        for p in self:
            origins = set(p.picking_ids.sale_id)
            p.numero_ordenes = len(origins)
            p.numero_ordenes_real = len(origins)
            p.cantidad_items = len(p.picking_ids)

    def write(self, vals):
        res = super().write(vals)
        if 'picking_ids' in vals:
            self.actualizar_campos_ordenes()
        return res

    def create(self, vals):
        record = super().create(vals)
        record.actualizar_campos_ordenes()
        return record

    @api.depends('create_date')
    def compute_mostrar(self):
        mostrar = self.search([], order='creade_date asc', limit=1)
        for record in self:
            record.mostrar = (record.id == mostrar.id)

    def write(self, values):
       for record in self:
           if 'state' in values and record.user_id and self.env.company.controlar_desface == 'si' and record.ordenes:
               oleada_editable = self.search([('user_id', '=', record.user_id.id),('ordenes','!=',False)],order='scheduled_date', limit=1)
               if record.id == oleada_editable.id:
                   return super(StockPickingBatch, self).write(values)
               else:
                   raise ValidationError("Error: Solo puede editar la oleada " + str(oleada_editable.name))
           else:
               return super(StockPickingBatch, self).write(values)