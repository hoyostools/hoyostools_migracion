# -*- coding: utf-8 -*-
#######################################
#######################################
import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api
from datetime import datetime
import pytz
import tempfile
import zipfile
from io import StringIO 
from io import BytesIO
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

#import xmltodict
import json
import re
import sys

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from base64 import b64encode
import base64
import json
from datetime import datetime

class ProductTemplate(models.Model): 

    _inherit = 'product.template'
    precioimp = fields.Float(
        string='Precio Final',
        compute='_compute_precioimp', 
        inverse='_inverse_precioimp', 
        store=False,
        #compute_sudo=True,
        copy=False,
        required=True,
        
    )
    @api.depends('list_price')
    def _compute_precioimp(self):
        today = fields.Date.today()
        for book in self:
          oldprice = book.precioimp
          try:
            book.precioimp=round(book.list_price+(book.list_price*((book.taxes_id[0].amount/100))),0)
          except:
            book.precioimp=book.list_price
    # This reverse method of _compute_age. Used to make age_days field editable
    # It is optional if you don't want to make compute field editable then you can remove this
    def _inverse_precioimp(self):
        today = fields.Date.today()
        for book in self:#self.filtered('precioimp'):
          oldprice=book.precioimp
          try:
            book.list_price = round(book.precioimp/(1+((book.taxes_id[0].amount/100))),0)
          except:
            book.list_price=book.precioimp
          
    @api.onchange('precioimp')  
    def _inverse_precioimp2(self):
        today = fields.Date.today()
        for book in self:#self.filtered('precioimp'):
          try:
            book.list_price = round(book.precioimp/(1+((book.taxes_id[0].amount/100))),0)          
          except:
            book.list_price=book.precioimp
