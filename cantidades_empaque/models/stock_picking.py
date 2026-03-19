from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _post_put_in_pack_hook(self, package_id):
        self.ensure_one()

        if (
            package_id
            and self.picking_type_id.auto_print_package_label
        ):
            cantidad = self.cajas_usadas

            package_ids = [package_id.id] * cantidad
            action = None
            if self.picking_type_id.package_label_to_print == 'pdf':
                action = self.env.ref(
                    "stock.label_package_template"
                ).report_action(package_ids, config=False)

            if self.picking_type_id.package_label_to_print == 'zpl':
                action = self.env.ref(
                    "stock.label_package_template"
                ).report_action(package_ids, config=False)

            if action:
                action.update({'close_on_report_download': True})
                return action

        return package_id

    def action_test_print_package(self):
        self.ensure_one()

        package = self.move_line_ids.result_package_id

        if not package:
            return False

        return self._post_put_in_pack_hook(package)