from odoo import api, models, fields, _
from collections import defaultdict
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_taxes(self):
        if self.product_id.product_tmpl_id.no_validar_bases:
            return self.tax_ids
        else:
            return super()._get_computed_taxes()


    @api.onchange('quantity', 'price_unit', 'discount')
    def calcular_retenciones(self):
        for line in self:
            move = line.move_id
            if move and move.state == 'draft':
                line._compute_tax_ids()

    @api.depends('product_id', 'product_uom_id')
    def _compute_tax_ids(self):
        super()._compute_tax_ids()

        for line in self:

            move = line.move_id

            if not move or move.move_type not in (
                'out_invoice', 'in_invoice', 'out_refund', 'in_refund'
            ):
                continue

            fiscal_position = move.fiscal_position_id

            if (
                move.journal_id.code != 'RMS'
                and fiscal_position
                and fiscal_position.tax_level_code_id.id != 1
            ):
                taxes_to_remove = line.tax_ids.filtered(
                    lambda t: (
                        t.base_check
                        and move.amount_untaxed != 0
                        and t.base_amount > move.amount_untaxed
                    )
                )
                taxes_reteiva = line.tax_ids.filtered(
                    lambda t: (
                        t.reteiva
                        and move.amount_untaxed != 0
                    )
                )

                if taxes_to_remove:
                    line.tax_ids -= taxes_to_remove

                if taxes_reteiva and fiscal_position.aplica_reteiva:
                    line.tax_ids += taxes_reteiva.impuesto_reteiva
                    


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for record in self:
            if record.move_type in (
                'out_invoice', 'in_invoice', 'out_refund', 'in_refund'
            ):
                record.invoice_line_ids._compute_tax_ids()
        return super().action_post()

    def _post(self, soft):
        for record in self:
            if record.move_type in (
                'out_invoice', 'in_invoice', 'out_refund', 'in_refund'
            ):
                record.invoice_line_ids._compute_tax_ids()
                _logger.warning("CALCULO RETENCIONES")
        return super()._post(soft)

    @api.onchange('line_ids', 'invoice_line_ids')
    def validar(self):
        for record in self:
            if record.move_type in (
                'out_invoice', 'in_invoice', 'out_refund', 'in_refund'
            ):
                record.invoice_line_ids._compute_tax_ids()

    def _compute_amount(self):
        res = super()._compute_amount()

        for record in self:
            if record.state == 'draft':
                record.invoice_line_ids._compute_tax_ids()

        return res