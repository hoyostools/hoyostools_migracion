# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inheriting model for adding a field to settings that allow to
            transfer stock from pos session """
    _inherit = 'res.config.settings'

    is_stock_transfer = fields.Boolean(related="pos_config_id.stock_transfer",
                                       string="Enable Stock Transfer",
                                       help="Enable if you want to transfer "
                                       "stock from PoS session", readonly=False)
