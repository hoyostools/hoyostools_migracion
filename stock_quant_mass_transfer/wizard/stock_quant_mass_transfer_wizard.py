from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class StockQuantMassTransferWizard(models.TransientModel):
    _name = 'stock.quant.mass.transfer.wizard'
    _description = 'Wizard traslado masivo quants'

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Tipo de Operación',
        required=True,
        domain="[('code','=','internal')]"
    )
    
    validar_albaranes = fields.Boolean(
        string='Validar Albaranes',
        default=False
    )

    transfer_mode = fields.Selection([
        ('different', 'Ubicaciones diferentes'),
        ('same', 'Una misma ubicación destino')
    ], string='Modo de Traslado', required=True, default='different')

    destination_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación Destino General'
    )

    line_ids = fields.One2many(
        'stock.quant.mass.transfer.line',
        'wizard_id',
        string='Líneas'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_ids = self.env.context.get('active_ids', [])
        quants = self.env['stock.quant'].browse(active_ids)

        lines = []

        for quant in quants:

            available_qty = quant.available_quantity

            if available_qty <= 0:
                continue

            lines.append((0, 0, {
                'product_id': quant.product_id.id,
                'source_location_id': quant.location_id.id,
                'available_qty': available_qty,
                'quantity': available_qty,
            }))

        res['line_ids'] = lines

        return res

    def action_transfer(self):

        self.ensure_one()

        pickings = self.env['stock.picking']

        if self.transfer_mode == 'same' and not self.destination_location_id:
            raise ValidationError(
                _('Debe seleccionar una ubicación destino.')
            )

        for line in self.line_ids:

            if line.quantity <= 0:
                continue

            available_qty = line.available_qty or 0.0

            rounding = (
                line.product_id.uom_id.rounding
                if line.product_id
                and line.product_id.uom_id
                and line.product_id.uom_id.rounding > 0
                else 0.01
            )

            if float_compare(
                line.quantity,
                available_qty,
                precision_rounding=rounding
            ) > 0:

                raise ValidationError(_(
                    'La cantidad a trasladar no puede ser superior '
                    'a la disponible del producto %s'
                ) % line.product_id.display_name)

            destination = (
                self.destination_location_id
                if self.transfer_mode == 'same'
                else line.destination_location_id
            )

            if not destination:
                raise ValidationError(_(
                    'Debe seleccionar ubicación destino.'
                ))

            # =====================================================
            # CREAR PICKING POR CADA PRODUCTO
            # =====================================================

            picking = self.env['stock.picking'].create({
                'picking_type_id': self.picking_type_id.id,
                'location_id': line.source_location_id.id,
                'location_dest_id': destination.id,
                'origin': _('Traslado Masivo'),
            })

            move = self.env['stock.move'].create({
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'location_id': line.source_location_id.id,
                'location_dest_id': destination.id,
                'picking_id': picking.id,
            })

            move._action_confirm()
            move._action_assign()

            # =====================================================
            # ASIGNAR CANTIDAD REAL
            # =====================================================

            for move_line in move.move_line_ids:
                move_line.quantity = line.quantity

            # =====================================================
            # VALIDAR PICKING
            # =====================================================

            if self.validar_albaranes:
                picking.button_validate()

            pickings |= picking

        # =========================================================
        # ABRIR PICKINGS CREADOS
        # =========================================================

        if len(pickings) == 1:

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': pickings.id,
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Traslados Internos'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', pickings.ids)],
        }

class StockQuantMassTransferLine(models.TransientModel):
    _name = 'stock.quant.mass.transfer.line'
    _description = 'Líneas traslado masivo'

    wizard_id = fields.Many2one(
        'stock.quant.mass.transfer.wizard'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        readonly=True
    )

    source_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación Origen',
        readonly=True
    )

    destination_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación Destino'
    )

    available_qty = fields.Float(
        string='Disponible',
        readonly=True
    )

    quantity = fields.Float(
        string='Cantidad a trasladar'
    )

    @api.constrains('quantity')
    def _check_quantity(self):

        for rec in self:

            rounding = (
                rec.product_id.uom_id.rounding
                if rec.product_id
                and rec.product_id.uom_id
                and rec.product_id.uom_id.rounding
                and rec.product_id.uom_id.rounding > 0
                else 0.01
            )

            if float_compare(
                rec.quantity,
                rec.available_qty,
                precision_rounding=rounding
            ) > 0:

                raise ValidationError(_(
                    'No puede trasladar más de la cantidad disponible.'
                ))