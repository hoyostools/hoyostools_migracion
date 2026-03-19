from odoo import models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    ubicacion_reab = fields.Many2one(
        related='product_id.product_tmpl_id.ubicacion_reab',
        string='Ubicación Reabastecimiento',
        store=False, readonly=True
    )

    regla_min_sugerida = fields.Float(
        related='product_id.product_tmpl_id.regla_min_sugerida',
        string='Regla Mín. Sugerida',
        store=False, readonly=True
    )

    cant_pack = fields.Integer(
        related='product_id.product_tmpl_id.cant_pack',
        string='Cantidad por Paca',
        store=False, readonly=True
    )
    
    regla_min = fields.Float(
        related='product_id.product_tmpl_id.regla_min',
        string='Regla Mín',
        store=False, readonly=True
    )
    
    regla_max = fields.Float(
        related='product_id.product_tmpl_id.regla_max',
        string='Regla Máx',
        store=False, readonly=True
    )
    
    alerta = fields.Boolean(
        related='product_id.product_tmpl_id.alerta',
        string='Alerta',
        store=False, readonly=True
    )
    
    
    
    tunel_clh = fields.Selection(
        related='ubicacion_reab.tunel',
        string='Túnel CLH',
        store=True,
        readonly=True
    )