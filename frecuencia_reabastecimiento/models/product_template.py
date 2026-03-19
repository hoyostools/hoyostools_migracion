from odoo import models, fields, api
import math

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ==========================================================
    # ======================= CLH ===============================
    # ==========================================================
    
    regla_min_sugerida = fields.Float(string='Regla Mínima Sugerida', compute='_compute_regla_min_sugerida', store=True)
    #"debe coger el campo promedio_consumo y dividirlo entre 24 para obtener el consumo diario. Luego, se debe calcular la regla mínima sugerida multiplicando el consumo diario por 4 días."
    pacas_sugeridas_min = fields.Float(string='Pacas Sugeridas Min', compute='_compute_pacas_sugeridas', store=True)
    #"numero de pacas sugeridas basado en la regla mínima sugerida y el contenido de cada paca cant_pack."
    ubicacion_reab = fields.Many2one(
        'stock.location',
        string='Ubicación Reabastecimiento',
        compute='_compute_ubicacion_reab',
        inverse='_set_ubicacion_reab',
        store=True
    )
    tunel_clh = fields.Selection(
        related='ubicacion_reab.tunel',
        string='Túnel CLH',
        store=True,
        readonly=True
    )
    qty_multiple_reab = fields.Float(
        string='Múltiplo de Pedido',
        compute='_compute_qty_multiple',
        inverse='_set_qty_multiple',
        store=True
    )

    regla_min = fields.Float(string='Regla Mínima', compute='_compute_reglas', inverse='_set_regla_min', store=True)
    regla_max = fields.Float(string='Regla Máxima', compute='_compute_reglas', inverse='_set_regla_max', store=True)

    dias_min = fields.Float(string='Días Mínimos', compute='_compute_dias', store=True)
    dias_max = fields.Float(string='Días Máximos', compute='_compute_dias', store=True)
    alerta = fields.Boolean(string='Alerta', compute='_compute_alerta', store=True)
    
    
    # ---------- CLH Cálculos ----------
    
    @api.depends('promedio_consumo')
    def _compute_regla_min_sugerida(self):
        for record in self:
            consumo_dia = (record.promedio_consumo or 0.0) / 24.0
            record.regla_min_sugerida = consumo_dia * 4 
    

    @api.depends('regla_min_sugerida', 'cant_pack')
    def _compute_pacas_sugeridas(self):
        for record in self:
            if record.regla_min_sugerida and record.cant_pack:
                record.pacas_sugeridas_min = math.floor(record.regla_min_sugerida / record.cant_pack)
            else:
                record.pacas_sugeridas_min = 0.0    

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_reglas(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            if orderpoint:
                record.regla_min = orderpoint.product_min_qty
                record.regla_max = orderpoint.product_max_qty
            else:
                record.regla_min = 0.0
                record.regla_max = 0.0

    def _set_regla_min(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            if orderpoint:
                orderpoint.product_min_qty = record.regla_min

    def _set_regla_max(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            if orderpoint:
                orderpoint.product_max_qty = record.regla_max
                
    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_ubicacion_reab(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            record.ubicacion_reab = orderpoint.location_id if orderpoint else False

    def _set_ubicacion_reab(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            if orderpoint:
                orderpoint.location_id = record.ubicacion_reab
                
    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_qty_multiple(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            record.qty_multiple_reab = orderpoint.qty_multiple if orderpoint else 0.0

    def _set_qty_multiple(self):
        for record in self:
            orderpoint = record._get_u05_orderpoint()
            if orderpoint:
                orderpoint.qty_multiple = record.qty_multiple_reab

    def _get_u05_orderpoint(self):
        self.ensure_one()
        return self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'in', self.product_variant_ids.ids),
            ('location_id.complete_name', 'ilike', 'CLH/Existencias/U05/')
        ], limit=1)

    @api.depends('regla_min', 'regla_max', 'promedio_consumo')
    def _compute_dias(self):
        for record in self:
            consumo_mes = record.promedio_consumo or 1.0
            consumo_dia = consumo_mes / 24.0
            record.dias_min = record.regla_min / consumo_dia if consumo_dia else 0.0
            record.dias_max = record.regla_max / consumo_dia if consumo_dia else 0.0

    @api.depends('dias_min')
    def _compute_alerta(self):
        for record in self:
            record.alerta = record.dias_min < 4.0
            
    # ==========================================================
    # ======================= EDI ===============================
    # ==========================================================
    
    promedio_consumo_edi = fields.Float(string='Promedio Consumo EDI')

    regla_min_sugerida_edi = fields.Float(
        string='Regla Mínima Sugerida EDI',
        compute='_compute_regla_min_sugerida_edi',
        store=True
    )

    pacas_sugeridas_min_edi = fields.Float(
        string='Pacas Sugeridas Min EDI',
        compute='_compute_pacas_sugeridas_edi',
        store=True
    )

    ubicacion_reab_edi = fields.Many2one(
        'stock.location',
        string='Ubicación Reab EDI',
        compute='_compute_ubicacion_reab_edi',
        inverse='_set_ubicacion_reab_edi',
        store=True
    )

    qty_multiple_reab_edi = fields.Float(
        string='Múltiplo Pedido EDI',
        compute='_compute_qty_multiple_edi',
        inverse='_set_qty_multiple_edi',
        store=True
    )

    regla_min_edi = fields.Float(
        string='Regla Mínima EDI',
        compute='_compute_reglas_edi',
        inverse='_set_regla_min_edi',
        store=True
    )

    regla_max_edi = fields.Float(
        string='Regla Máxima EDI',
        compute='_compute_reglas_edi',
        inverse='_set_regla_max_edi',
        store=True
    )

    dias_min_edi = fields.Float(
        string='Días Mínimos EDI',
        compute='_compute_dias_edi',
        store=True
    )

    dias_max_edi = fields.Float(
        string='Días Máximos EDI',
        compute='_compute_dias_edi',
        store=True
    )

    alerta_edi = fields.Boolean(
        string='Alerta EDI',
        compute='_compute_alerta_edi',
        store=True
    )

    # ---------- EDI Cálculos ----------

    @api.depends('promedio_consumo_edi')
    def _compute_regla_min_sugerida_edi(self):
        for record in self:
            consumo_dia = (record.promedio_consumo_edi or 0.0) / 24.0
            record.regla_min_sugerida_edi = consumo_dia * 4

    @api.depends('regla_min_sugerida_edi', 'cant_pack')
    def _compute_pacas_sugeridas_edi(self):
        for record in self:
            if record.regla_min_sugerida_edi and record.cant_pack:
                record.pacas_sugeridas_min_edi = math.floor(
                    record.regla_min_sugerida_edi / record.cant_pack
                )
            else:
                record.pacas_sugeridas_min_edi = 0.0

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_reglas_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            record.regla_min_edi = op.product_min_qty if op else 0.0
            record.regla_max_edi = op.product_max_qty if op else 0.0

    def _set_regla_min_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            if op:
                op.product_min_qty = record.regla_min_edi

    def _set_regla_max_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            if op:
                op.product_max_qty = record.regla_max_edi

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_ubicacion_reab_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            record.ubicacion_reab_edi = op.location_id if op else False

    def _set_ubicacion_reab_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            if op:
                op.location_id = record.ubicacion_reab_edi

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_qty_multiple_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            record.qty_multiple_reab_edi = op.qty_multiple if op else 0.0

    def _set_qty_multiple_edi(self):
        for record in self:
            op = record._get_u01_orderpoint()
            if op:
                op.qty_multiple = record.qty_multiple_reab_edi

    def _get_u01_orderpoint(self):
        self.ensure_one()
        return self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'in', self.product_variant_ids.ids),
            ('location_id.complete_name', 'ilike', 'EDI/Existencias/U01/')
        ], limit=1)

    @api.depends('regla_min_edi', 'regla_max_edi', 'promedio_consumo_edi')
    def _compute_dias_edi(self):
        for record in self:
            consumo_dia = (record.promedio_consumo_edi or 0.0) / 24.0
            record.dias_min_edi = record.regla_min_edi / consumo_dia if consumo_dia else 0.0
            record.dias_max_edi = record.regla_max_edi / consumo_dia if consumo_dia else 0.0

    @api.depends('dias_min_edi')
    def _compute_alerta_edi(self):
        for record in self:
            record.alerta_edi = record.dias_min_edi < 4.0
            
            
    # ==========================================================
    # ======================= PTV ===============================
    # ==========================================================

    regla_min_sugerida_ptv = fields.Float(string='Regla Mínima Sugerida PTV', compute='_compute_regla_min_sugerida_ptv', store=True)
    pacas_sugeridas_min_ptv = fields.Float(string='Pacas Sugeridas Min PTV', compute='_compute_pacas_sugeridas_ptv', store=True)

    regla_min_ptv = fields.Float(string='Regla Mínima PTV', compute='_compute_reglas_ptv', inverse='_set_regla_min_ptv', store=True)
    regla_max_ptv = fields.Float(string='Regla Máxima PTV', compute='_compute_reglas_ptv', inverse='_set_regla_max_ptv', store=True)

    qty_multiple_reab_ptv = fields.Float(string='Múltiplo Pedido PTV', compute='_compute_qty_multiple_ptv', inverse='_set_qty_multiple_ptv', store=True)
    ubicacion_reab_ptv = fields.Many2one('stock.location', string='Ubicación Reab PTV', compute='_compute_ubicacion_reab_ptv', inverse='_set_ubicacion_reab_ptv', store=True)

    dias_min_ptv = fields.Float(string='Días Mínimos PTV', compute='_compute_dias_ptv', store=True)
    dias_max_ptv = fields.Float(string='Días Máximos PTV', compute='_compute_dias_ptv', store=True)

    alerta_ptv = fields.Boolean(string='Alerta PTV', compute='_compute_alerta_ptv', store=True)
    
    # ---------- PTV Cálculos ----------
    
    def _get_ptv_orderpoint(self):
        self.ensure_one()
        return self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'in', self.product_variant_ids.ids),
            ('location_id.complete_name', 'ilike', 'PTV/Existencias')
        ], limit=1)

    @api.depends('average_ptv')
    def _compute_regla_min_sugerida_ptv(self):
        for record in self:
            consumo_dia = (record.average_ptv or 0.0) / 24.0
            record.regla_min_sugerida_ptv = consumo_dia * 4

    @api.depends('regla_min_sugerida_ptv', 'cant_pack')
    def _compute_pacas_sugeridas_ptv(self):
        for record in self:
            if record.regla_min_sugerida_ptv and record.cant_pack:
                record.pacas_sugeridas_min_ptv = math.floor(record.regla_min_sugerida_ptv / record.cant_pack)
            else:
                record.pacas_sugeridas_min_ptv = 0.0

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_reglas_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            record.regla_min_ptv = op.product_min_qty if op else 0.0
            record.regla_max_ptv = op.product_max_qty if op else 0.0

    def _set_regla_min_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            if op:
                op.product_min_qty = record.regla_min_ptv

    def _set_regla_max_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            if op:
                op.product_max_qty = record.regla_max_ptv

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_qty_multiple_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            record.qty_multiple_reab_ptv = op.qty_multiple if op else 0.0

    def _set_qty_multiple_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            if op:
                op.qty_multiple = record.qty_multiple_reab_ptv

    @api.depends('product_variant_ids.orderpoint_ids')
    def _compute_ubicacion_reab_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            record.ubicacion_reab_ptv = op.location_id if op else False

    def _set_ubicacion_reab_ptv(self):
        for record in self:
            op = record._get_ptv_orderpoint()
            if op:
                op.location_id = record.ubicacion_reab_ptv

    @api.depends('regla_min_ptv', 'regla_max_ptv', 'average_ptv')
    def _compute_dias_ptv(self):
        for record in self:
            consumo_dia = (record.average_ptv or 0.0) / 24.0
            record.dias_min_ptv = record.regla_min_ptv / consumo_dia if consumo_dia else 0.0
            record.dias_max_ptv = record.regla_max_ptv / consumo_dia if consumo_dia else 0.0

    @api.depends('dias_min_ptv')
    def _compute_alerta_ptv(self):
        for record in self:
            record.alerta_ptv = record.dias_min_ptv < 4.0