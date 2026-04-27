# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
##########################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductCatalogs(models.TransientModel):
    _name = 'product.catalogs'
    _description = "Product Catalogs"

    catalog_type = fields.Selection([
        ('product', 'Product'),
        ('category', 'Category')
    ], default='product', string='Catalog Type', required=True)

    product_ids = fields.Many2many('product.template', string="Products")
    product_category_ids = fields.Many2many('product.category', string="Category")
    product_description = fields.Boolean(string="Description", default=False)
    product_internal_reference = fields.Boolean(string="Internal Reference", default=False)

    style = fields.Selection([
        ('list', 'List'),
        ('card', 'Card')
    ], default='list', string='Style', required=True)

    image_size = fields.Selection([
        ('small', 'Small 5 Box Per Row'),
        ('medium', 'Medium 3 Box Per Row'),
        ('large', 'Large 2 Box Per Row')
    ], default='small')

    frontpage = fields.Boolean(string="Frontpage", default=False)
    catalog_frontpage_id = fields.Many2one('catalog.frontpage', string="Frontpage Image")
    display_title = fields.Boolean(string="Display Title", default=True)
    frontpage_title = fields.Char(string="Frontpage Title")
    product_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    show_price = fields.Boolean(string="Show Price", default=True)
    show_link = fields.Boolean(string="Show Link", default=True)

    # **Campos computados para manejar la visibilidad en Odoo 17**
    show_product_ids = fields.Boolean(compute="_compute_visibility", store=True)
    show_product_category_ids = fields.Boolean(compute="_compute_visibility", store=True)
    show_image_size = fields.Boolean(compute="_compute_visibility", store=True)

    @api.depends('catalog_type', 'style')
    def _compute_visibility(self):
        for record in self:
            record.show_product_ids = record.catalog_type != 'category'
            record.show_product_category_ids = record.catalog_type != 'product'
            record.show_image_size = record.style != 'list'

    def print_catalog(self):
        self.ensure_one()
        datas = {
            'product_ids': self.product_ids.ids
        }
        return self.env.ref('product_catalogs.action_product_catalogs_report').report_action(self, data=None)
