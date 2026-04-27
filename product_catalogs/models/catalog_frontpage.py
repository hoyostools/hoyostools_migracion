# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class CatalogFrontpage(models.Model):
    _name = 'catalog.frontpage'
    _description = "Catalog Frontpage"

    name = fields.Char(string="Name", required=True, attachment=False, stored=True)
    frontpage = fields.Binary(string="Frontpage", attachment=False, stored=True)
