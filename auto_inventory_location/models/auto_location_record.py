from odoo import models, fields, api


class AutoLocationRecord(models.Model):
    _name = "auto.location.record"
    _description = "Registro de Auto Ubicación"

    product_id = fields.Many2one("product.product")
    default_code = fields.Char(related="product_id.default_code")

    picking_id = fields.Many2one("stock.picking")
    purchase_id = fields.Many2one("purchase.order")

    location_id = fields.Many2one("stock.location")
    move_id = fields.Many2one("stock.move")
    product_max_qty = fields.Float()

    fecha_llegada = fields.Datetime()
    cantidad_recibida = fields.Float()
    cantidad_ubicada = fields.Float()

    cantidad_pendiente = fields.Float(
        compute="_compute_pendiente",
        store=True
    )

    porcentaje_llenado = fields.Float(
        string="Porcentaje de Llenado (%)",
        compute="_compute_porcentaje_llenado",
        store=True
    )

    ranking_rotacion = fields.Float()

    prioridad = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorite')
    ],compute='_compute_prioridad', default='0', string="Prioridad")

    sin_regla = fields.Boolean()
    liberado = fields.Boolean()

    tiempo_sin_ubicar = fields.Integer(
        compute="_compute_tiempo",
        store = False
    )
    origen_bienes = fields.Selection(
        [
            ("nacional", "Nacional"),
            ("importado", "Importado"),
        ],
        string="Origen de los bienes",
        compute="_compute_origen_bienes",
        store=True
    )

    @api.depends("product_id")
    def _compute_origen_bienes(self):

        for rec in self:

            country = rec.product_id.product_tmpl_id.country_of_origin

            if not country:
                rec.origen_bienes = False
                continue

            if country.code == "CO":
                rec.origen_bienes = "nacional"
            else:
                rec.origen_bienes = "importado"

    # -------------------------
    # PENDIENTE
    # -------------------------

    @api.depends("cantidad_recibida", "location_id.quant_ids.quantity", "cantidad_ubicada")
    def _compute_pendiente(self):
        for rec in self:
            rec.cantidad_pendiente = rec.cantidad_recibida - rec.cantidad_ubicada
            if rec.cantidad_pendiente < 0:
                rec.cantidad_pendiente = 0

    @api.depends("move_id.state")
    def _compute_pendiente(self):
        for rec in self:
            if rec.move_id.state == 'done':
                rec.cantidad_ubicada = rec.move_id.quantity

    # -------------------------
    # PORCENTAJE LLENADO
    # -------------------------

    @api.depends("product_id", "location_id.quant_ids.quantity", "product_max_qty")
    def _compute_porcentaje_llenado(self):

        for rec in self:

            if not rec.product_id or not rec.location_id:
                rec.porcentaje_llenado = 0
                continue

            ubicacion = rec.location_id.quant_ids.filtered(lambda b: b.product_id == rec.product_id)
            cantidad_actual = ubicacion.quantity

            if rec.product_max_qty:
                rec.porcentaje_llenado = (
                    cantidad_actual / rec.product_max_qty
                ) * 100
            else:
                rec.porcentaje_llenado = 0

    # -------------------------
    # PRIORIDAD
    # -------------------------

    @api.depends("porcentaje_llenado", "ranking_rotacion")
    def _compute_prioridad(self):

        for rec in self:

            if rec.porcentaje_llenado <= 50 and rec.ranking_rotacion <= 100:
                rec.prioridad = '1'
            else:
                rec.prioridad = '0'

    # -------------------------
    # TIEMPO SIN UBICAR
    # -------------------------

    @api.depends("fecha_llegada")
    def _compute_tiempo(self):

        now = fields.Datetime.now()

        for rec in self:

            if rec.fecha_llegada:
                delta = now - rec.fecha_llegada
                rec.tiempo_sin_ubicar = delta.days
            else:
                rec.tiempo_sin_ubicar = 0
