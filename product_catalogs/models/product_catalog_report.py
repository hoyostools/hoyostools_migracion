# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

   
    def open_wizard(self):
        ctx = self._context.copy()
        new_wizard = self.env['product.catalogs'].create(
            {'product_ids': self.ids})
        compose_form = self.env.ref(
            'product_catalogs.view_product_catalogs_form')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': compose_form.id,
            'res_model': 'product.catalogs',
            'res_id': new_wizard.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }