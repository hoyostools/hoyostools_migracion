from odoo import fields, models, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    ranking_product_id = fields.Integer(string='Ranking', related='product_id.ranking', store=True)
    responsible_id = fields.Many2one(
        related='product_id.responsible_id',
        store=True,
        string='Responsable',
        readonly=False
    )
    sale_ok = fields.Boolean(
        related='product_id.sale_ok',
        store=True,
        string='Se puede vender',
        readonly=False
    )
    purchase_ok = fields.Boolean(
        related='product_id.purchase_ok',
        store=True,
        string='Se puede comprar',
        readonly=False
    )
    promedio_consumo = fields.Integer(
        related='product_id.promedio_consumo',
        store=True,
        string='Prom. Consumo',
        readonly=False
    )
    cant_pack = fields.Integer(
        related='product_id.cant_pack',
        store=True,
        string='Cant. Paca',
        readonly=False,
    )
    stand_ptv = fields.Char(related='product_tmpl_id.stand_ptv', store=True,)

    inventory_projection = fields.Char(string='Proyección inventario', compute=False, store=True)
    proyeccion_inventario = fields.Float(related='product_id.proyeccion_inventario', string='Proy. Inventario')

    last_update_inv_proj = fields.Datetime()

    # @api.onchange('qty_forecast', 'promedio_consumo')
    # @api.depends('qty_forecast', 'promedio_consumo')
    def _compute_inventory_projection(self):
        for record in self:
            # Calcula el inventory_projection de warehouse
            if record.promedio_consumo:
                record.inventory_projection = str(round(record.qty_forecast / record.promedio_consumo, 3)) if record.promedio_consumo != 0 else '0'
            else:
                record.inventory_projection = 'Cantidad Paca No Definida'
            record.last_update_inv_proj = fields.Datetime.now()

            if record.warehouse_id.id == self.env.ref('stock.warehouse0').id:
                record.product_id.product_tmpl_id.inventory_projection = record.inventory_projection

            # Actualizar la proyección de inventario en el producto
            product = record.product_id
            product.proyeccion_inventario = (
                        product.free_qty / product.promedio_consumo) if product.promedio_consumo != 0 else 0


    @api.depends('product_id', 'location_id', 'product_id.stock_move_ids', 'product_id.stock_move_ids.state',
                 'product_id.stock_move_ids.date', 'product_id.stock_move_ids.product_uom_qty')
    def _compute_qty(self):
        super(StockWarehouse, self)._compute_qty()
        # self._compute_inventory_projection()



    def compute_update_inventory_projection(self):
        for record in self.env["stock.warehouse.orderpoint"].search([]):
            if record.promedio_consumo:
                record.inventory_projection = str(round(record.qty_forecast / record.promedio_consumo, 3)) if record.promedio_consumo != 0 else '0'
            else:
                record.inventory_projection = 'Cantidad Paca No Definida'