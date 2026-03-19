from odoo import api, fields, models

class StockScrap(models.Model):
    _inherit = "stock.scrap"

    observation = fields.Text(string="Observación")

    # @api.depends('company_id', 'reason_code_id')
    def _compute_scrap_location_id(self):
        super()._compute_scrap_location_id()

        for scrap in self:
            if scrap.reason_code_id and scrap.reason_code_id.location_id:
                scrap.scrap_location_id = scrap.reason_code_id.location_id

    @api.onchange("reason_code_id")
    def _onchange_reason_code_id(self):
        if self.reason_code_id and self.reason_code_id.location_id:
            self.scrap_location_id = self.reason_code_id.location_id

    def _update_scrap_reason_code_location(self, vals):
        reason_code_id = vals.get("reason_code_id")
        if reason_code_id:
            reason_code = self.env["scrap.reason.code"].browse(reason_code_id)
            if reason_code.location_id and "scrap_location_id" not in vals:
                vals["scrap_location_id"] = reason_code.location_id.id

    def write(self, vals):
        self._update_scrap_reason_code_location(vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._update_scrap_reason_code_location(vals)
        return super().create(vals_list)

    def action_validate(self):
        res = super().action_validate()
        moves = self.env['account.move'].search([
            ('journal_id', '=', 8),
            ('stock_move_id', 'in', self.move_ids.ids)
        ])

        for move in moves:
            for line in move.line_ids:
                if line.name:
                    line.name = line.name.replace('(modification of past move)', '').strip()
                    if self.observation:
                        line.name = f"{line.name} - {self.observation}".strip()
        return res
