# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from datetime import date, time, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError,Warning
import logging
import math

_logger = logging.getLogger(__name__)
	
class web_loyalty_setting(models.Model):
	_name = 'web.loyalty.setting'
	_description = 'web loyalty setting'
		
	name  = fields.Char('Name' ,default='Configuration for Website Loyalty Management')
	product_id  = fields.Many2one('product.product','Product', domain = [('type', '=', 'service')],required=True)
	issue_date  =  fields.Date(default=fields.date.today(),required=True)
	expiry_date  = fields.Date('Expiry date',required=True)
	loyalty_basis_on = fields.Selection([('amount', 'Purchase Amount'), ('web_category', 'Website Product Categories')], string='Loyalty Basis On',required=True)
	active  =  fields.Boolean('Active')
	loyality_amount = fields.Float('Amount')
	amount_footer = fields.Float('Footer Amount', related='loyality_amount')
	redeem_ids = fields.One2many('web.redeem.rule', 'loyality_id', 'Redemption Rule')

	@api.constrains('issue_date','expiry_date','active')
	def check_date(self):
		if self.expiry_date < self.issue_date :
			msg = _("Expiry Date should not be smaller than Issue Date. please change dates.")
			raise ValidationError(msg)

		flag = False
		for record in self.search([]):
			if record.active  and self.id != record.id:
				if (record.issue_date <= self.issue_date <=record.expiry_date) or (record.issue_date <= self.expiry_date <=record.expiry_date) : 
					flag = True

				if record.issue_date >= self.issue_date <=record.expiry_date : 
					flag = True

		if flag: 	
			msg = _("You can not apply two Loyalty Configuration within same date range please change dates.")
			raise ValidationError(msg)

	@api.model
	def search_loyalty_product(self,product_id):
		
		product = self.product_id.search([('id','=',product_id)])

		return product.id

class web_redeem_rule(models.Model):
	_name = 'web.redeem.rule' 
	_description = 'web redeem rule'   
	
	name = fields.Char('Name' ,default='Point Redemption Configuration')
	min_amt = fields.Float('Minimum Points')
	max_amt = fields.Float('Maximum Points')
	reward_amt = fields.Float('Redemption Amount')
	loyality_id = fields.Many2one('web.loyalty.setting', 'Loyalty ID')

	@api.onchange('max_amt','min_amt')
	def _check_amt(self):
		if (self.max_amt !=0):
			if(self.min_amt > self.max_amt):
				msg = _("Minimum Point is not larger than Maximum Point")
				raise ValidationError(msg)
		return

	@api.onchange('reward_amt')
	def _check_reward_amt(self):
		if self.reward_amt !=0:
			if self.reward_amt <= 0:			
					msg = _("Reward amount is not a zero or less than zero")
					raise ValidationError(msg)
		return

	@api.constrains('min_amt','max_amt')
	def _check_points(self):

		for line in self:
			record = self.env['web.redeem.rule'].search([('loyality_id','=',line.loyality_id.id)])
			for rec in record :
				if line.id != rec.id:
					if (rec.min_amt <= line.min_amt  <= rec.max_amt) or (rec.min_amt <=line.max_amt  <= rec.max_amt):
						msg = _("You can not create Redemption Rule with same points range.")
						raise ValidationError(msg)
						return
					
class web_loyalty_history(models.Model):
	_name = 'web.loyalty.history'
	_rec_name = 'order_id'
	_order = 'id desc'
	_description = 'web loyalty history'   
		
	order_id  = fields.Many2one('sale.order','Sale Order')
	partner_id  = fields.Many2one('res.partner','Customer')
	date  =  fields.Datetime(default = datetime.now(), )
	transaction_type = fields.Selection([('credit', 'Credit'), ('debit', 'Debit')], string='Transaction Type', help='credit/debit loyalty transaction in Website.')
	points = fields.Integer('Loyalty Points')
	amount = fields.Char('Amount')
	currency_id = fields.Many2one('res.currency', 'Currency')
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, required=True)
		
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
