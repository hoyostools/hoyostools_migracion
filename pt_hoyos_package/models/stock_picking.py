from odoo import api, fields, models, tools, _



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _post_put_in_pack_hook(self, delivery_package):
        result = super()._post_put_in_pack_hook(delivery_package)

        if isinstance(delivery_package, dict) and delivery_package.get('id'):
            package = self.env['stock.quant.package'].browse(
                delivery_package['id'])

            if package.exists() and not package.picking_id:
                package.picking_id = self.id

        return result



