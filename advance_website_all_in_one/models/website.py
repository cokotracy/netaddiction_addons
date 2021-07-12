# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from datetime import date, time, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError,Warning
import logging
import math

_logger = logging.getLogger(__name__)
	

class res_partner(models.Model):
	_inherit = 'res.partner'

	loyalty_points = fields.Integer('Loyalty Points')
	loyalty_amount = fields.Float('Loyalty Amount')


class web_category(models.Model):
	_inherit = 'product.public.category'

	Minimum_amount  = fields.Integer("Amount For loyalty Points")
	amount_footer = fields.Integer('Amount', related='Minimum_amount')


class Website(models.Model):
	_inherit = 'website'
		
	def get_loyalty_balance(self,order): 
		today_date = datetime.today().date() 
		amt_total = order.amount_total
		partner_id =order.partner_id
		loyalty_points = 0.0
		plus_points = 0.0
		total_loyalty = 0.0
		company_currency = self.company_id.currency_id
		web_currency = self.get_current_pricelist().currency_id

		config = self.env['web.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
							('expiry_date', '>=', today_date )])
		if not self.is_public_user():
			if config : 
				if config.loyalty_basis_on == 'amount' :
					if config.loyality_amount > 0 :
						if company_currency.id != web_currency.id:
							price = amt_total
							new_rate = (price*company_currency.rate)/web_currency.rate
						else:
							new_rate = amt_total
						plus_points =  int( new_rate / config.loyality_amount )
						total_loyalty = partner_id.loyalty_points + plus_points

				if config.loyalty_basis_on == 'web_category' :
					for line in  order.order_line:
						prod_categs = line.product_id.public_categ_ids
						for c in prod_categs :
							if c.Minimum_amount > 0 :
								if company_currency.id != web_currency.id:
									price = line.price_subtotal
									new_rate = (price*company_currency.rate)/web_currency.rate
								else:
									new_rate = line.price_subtotal
								plus_points += int(new_rate / c.Minimum_amount)

					total_loyalty = partner_id.loyalty_points + plus_points
		return [plus_points,total_loyalty]
					
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
