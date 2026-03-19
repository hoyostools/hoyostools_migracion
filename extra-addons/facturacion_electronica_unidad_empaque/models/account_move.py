from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_dict_invoicehead_dian(self, totales):
        datos = super(AccountMove, self).create_dict_invoicehead_dian(totales)
        paquetes = []
        for picking in self.picking_ids:
            if picking.packaging_order_observation:
                paquetes.append(picking.packaging_order_observation)
        datos['InvoiceComment6'] = ', '.join(paquetes) if paquetes else ''
        return datos
