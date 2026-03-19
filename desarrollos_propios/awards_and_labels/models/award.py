from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class Award(models.Model):
    _name = 'awards_and_labels.award'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Premio'

    name = fields.Char(string='Nombre del Premio', required=True, tracking=True)
    fecha_evento_inicio = fields.Date(string="Fecha Evento Inicio", help='Fecha de Inicio del evento.', tracking=True)
    fecha_evento_fin = fields.Date(string="Fecha Evento Fin", help='Fecha de Fin del evento', tracking=True)
    condicion = fields.Selection(
        [('marca', 'Marca'), ('categoria', 'Categoría'), ('producto', 'Producto'), ('etiqueta', 'Etiqueta de producto'), ('pricelist', 'Lista de precios')],
        string='Condición',
        help='''
        - Si seleccionas una codicion y no pones valor, y el campo Acomulable es Falso entonces va dar una boleta por la condicion seleccionada.
        - Si seleccionas una condicion y no pones valor, y el campo Acomulable es Verdadero entonces va dar una boleta por cada unidad de la condicion seleccionada.
        - Si no seleccionas una condicion debes poner un valor para poder hacer la validacion.
        ''',
        tracking=True
    )
    fecha_hora_sorteo = fields.Datetime(string="Fecha y Hora Sorteo", help='Fecha del Sorteo de este Premio', tracking=True)
    valor = fields.Float(string='Valor', help='Ingresa el valor base de generacion.', tracking=True)
    acomulable = fields.Boolean(string="Acumulable", help='Marque la casilla si quieres una boleta por cada valor indicado', tracking=True)

    product_brand_ids = fields.Many2many(
        'product.brand',
        string='Marca',
        tracking=True
    )
    categ_ids = fields.Many2many(
        'product.category',
        string='Categoría',
        tracking=True
    )
    product_ids = fields.Many2many(
        'product.template',
        string='Productos',
        tracking=True
    )
    product_tag_ids = fields.Many2many(
        'product.tag', 
        string="Etiqueta de producto",
        tracking=True
    )
    pricelist_ids = fields.Many2many(
        'product.pricelist',
        string='Listas de precios'
    )
    buzon = fields.Selection(
        selection=[(str(i), str(i)) for i in range(1, 51)],
        string="Buzón",
        required=True,
        help='Seleccione el buzon asignado para este premio.',
        tracking=True
    )
    active = fields.Boolean(string='Activo', default=True, tracking=True)
    show_brand = fields.Boolean(compute='_compute_show_fields')
    show_categ = fields.Boolean(compute='_compute_show_fields')
    show_product = fields.Boolean(compute='_compute_show_fields')
    show_tag = fields.Boolean(compute='_compute_show_fields')
    show_price_list = fields.Boolean(compute='_compute_show_fields')
    
    @api.constrains('fecha_evento_inicio', 'fecha_evento_fin', 'fecha_hora_sorteo')
    def _check_fecha_hora_sorteo_within_range(self):
        for rec in self:
            if rec.fecha_evento_inicio and rec.fecha_evento_fin and rec.fecha_hora_sorteo:
                if not (rec.fecha_evento_inicio <= rec.fecha_hora_sorteo.date() <= rec.fecha_evento_fin):
                    raise ValidationError(
                        "La fecha y hora del sorteo debe estar dentro del rango de fechas del evento."
                    )

    @api.constrains('fecha_evento_inicio', 'fecha_evento_fin')
    def _check_fecha_evento(self):
        for rec in self:
            if rec.fecha_evento_inicio and rec.fecha_evento_fin:
                if rec.fecha_evento_fin < rec.fecha_evento_inicio:
                    raise ValidationError("La fecha de fin no puede ser menor a la fecha de inicio.")
    
    @api.constrains('condicion', 'product_brand_ids', 'categ_ids', 'product_tag_ids', 'product_ids', 'pricelist_ids')
    def _check_required_fields(self):
        for rec in self:
            if rec.condicion == 'marca' and not rec.product_brand_ids:
                raise ValidationError(_("Debe seleccionar una marca."))
            if rec.condicion == 'categoria' and not rec.categ_ids:
                raise ValidationError(_("Debe seleccionar una categoría."))
            if rec.condicion == 'etiqueta' and not rec.product_tag_ids:
                raise ValidationError(_("Debe seleccionar una etiqueta."))
            if rec.condicion == 'producto' and not rec.product_ids:
                raise ValidationError(_("Debe seleccionar un producto."))
            if rec.condicion == 'pricelist' and not rec.pricelist_ids:
                raise ValidationError(_("Debe seleccionar una Lista de Precios"))
    
    @api.depends('condicion')
    def _compute_show_fields(self):
        for rec in self:
            rec.show_brand = rec.condicion == 'marca'
            rec.show_categ = rec.condicion == 'categoria'
            rec.show_tag = rec.condicion == 'etiqueta'
            rec.show_product = rec.condicion == 'producto'
            rec.show_price_list = rec.condicion == 'pricelist'

    @api.constrains('buzon')
    def _check_buzon_unique(self):
        for rec in self:
            if rec.buzon:
                otros = self.search([('buzon', '=', rec.buzon), ('id', '!=', rec.id)])
                if otros:
                    raise ValidationError(f"El Buzón {rec.buzon} ya está asignado a otro premio. Debe ser único.")
                
    @api.model
    def create(self, vals):
        # Crea el premio normalmente
        award = super().create(vals)

        # Busca todos los contactos
        partners = self.env['res.partner'].search([])

        # Crea la relación para cada contacto
        for partner in partners:
            self.env['awards_and_labels.res_partner_award'].create({
                'partner_id': partner.id,
                'award_id': award.id,
                'cantidad': 0,
            })

        return award
    
    def action_view_participants(self):
        self.ensure_one()
        return {
            'name': f'Participantes Buzón {self.buzon}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [
                ('award_ids.award_id', '=', self.id),
                ('award_ids.cantidad', '>', 0)
            ],
            'context': {'search_default_groupby_award': 1}
        }