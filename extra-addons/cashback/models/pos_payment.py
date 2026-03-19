# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from odoo.exceptions import RedirectWarning, UserError, ValidationError


import logging



_logger = logging.getLogger(__name__)



class PosPyament(models.Model):
	_inherit = 'pos.payment'

	@api.model_create_multi
	def create(self, vals_list):
		
		res = super(PosPyament,self).create(vals_list)
		return res