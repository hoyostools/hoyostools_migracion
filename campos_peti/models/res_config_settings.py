from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import os
from datetime import datetime
import base64


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_negative_credit = fields.Boolean(default=False)
    check_limit_with_qty_delivered = fields.Boolean(default=False)
    product_restriction = fields.Boolean(default=False)
    module_cloud_base_documents = fields.Binary()
    check_stock = fields.Boolean(default=False)
    brand_use_level = fields.Char()
    sale_order_status = fields.Char()
    outgoing_routing_order = fields.Char()
    stock_reservation_strategy = fields.Char()
    module_google_drive_odoo = fields.Char()
    module_onedrive = fields.Char()
    module_owncloud_odoo = fields.Char()
    module_outgoing_routing = fields.Char()
    custom_package_name = fields.Char()
    group_cloud_base_share = fields.Char()
    base_version = fields.Char()
    max_lines_per_order = fields.Integer()
    cloud_log_days = fields.Integer()
    sale_order_line_record_limit = fields.Integer()
    module_dropbox = fields.Char()
    group_cloud_base_tags = fields.Char()