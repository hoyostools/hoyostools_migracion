# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, tools
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import random
import base64
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from collections import defaultdict
from odoo.tools import float_is_zero


class PosSessionInherit(models.Model):
	_inherit = 'pos.session'

	def _loader_params_pos_payment_method(self):
		result = super()._loader_params_pos_payment_method()
		result['search_params']['fields'].extend(['is_cashback'])
		return result

	def _loader_params_res_partner(self):
		result = super()._loader_params_res_partner()
		result['search_params']['fields'].extend(['active_cashback_limit',  'blocking_amount', 'custom_cashback', 'attended_event', 'days_unreconciled_10','over_permision_unreconciled_10'])
		return result
