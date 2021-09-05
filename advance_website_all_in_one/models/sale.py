# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from datetime import date, time, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError,Warning
import logging
import math

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	order_credit_points = fields.Integer(string='Order Credit Points')
	order_redeem_points = fields.Integer(string='Order Redeemed Points')
	redeem_value = fields.Float(string='Redeem point value')

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	discount_line = fields.Boolean(string='Discount line',readonly=True)
	voucher_line = fields.Boolean(string='Voucher line',readonly=True)
	redeem_points = fields.Integer(string='Redeem Points')
	redeem_value = fields.Float(string='Redeem point value')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: