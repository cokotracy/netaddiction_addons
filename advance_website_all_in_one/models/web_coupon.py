# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import random
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ProductTemp(models.Model):
	_inherit = 'product.template'

	is_coupon_product = fields.Boolean(string='Coupon Product')
	coupon_ok = fields.Boolean("Is a Gift Coupon",default=False)

	@api.model
	def create(self, vals):
		res = super(ProductTemp, self).create(vals)
		if vals.get("is_coupon_product"):
			res.write({
				'sale_ok' : False
				})
		if vals.get('sale_ok'):
			res.write({
				'is_coupon_product' : False
				})
		if vals.get('sale_ok') and vals.get('is_coupon_product'):
			raise UserError(_('Product Can be Sold or Coupon Product !!!!'))
		return res


	def write(self, vals):
		res = super(ProductTemp, self).write(vals)
		if vals.get("is_coupon_product"):
			self.update({
				'sale_ok' : False
				})
		if vals.get('sale_ok'):
			self.update({
				'is_coupon_product' : False
				})
		if vals.get('sale_ok') and vals.get('is_coupon_product'):
			raise UserError(_('Product Can be Sold or Coupon Product !!!!'))
		return res


class web_gift_coupon(models.Model):
	_name = 'web.gift.coupon'
	_description = 'web gift coupon'

	_sql_constraints = [
		('name', 'UNIQUE(name)', "coupon already exist please enter different name for this coupon."),
	]
	
	
	def print_report_coupons(self):
		return self.env.ref('advance_website_all_in_one.action_report_print_gift_coupon').report_action(self)


	@api.constrains('amount','issue_date','expiry_date','max_amount')
	def _check_config(self):
		if self.expiry_date and self.issue_date:
			if self.expiry_date < self.issue_date:
				raise Warning(_( "Please Enter Valid Date.Expiry Date Should not be greater than Issue Date."))

	@api.model
	def create(self, vals):
		rec = super(web_gift_coupon,self).create(vals)
		code =(random.randrange(1111111111111,9999999999999))
		rec.write({'c_barcode':str(code)})
		return rec


	name  = fields.Char('Name')
	product_id  = fields.Many2one('product.product','Product', domain = [('type', '=', 'service'),('is_coupon_product', '=', True)])
	c_barcode = fields.Char(string="Coupon Barcode")
	c_barcode_img = fields.Binary('Coupon Barcode Image')
	user_id  =  fields.Many2one('res.users' ,'Created By',default  = lambda self: self.env.user)
	issue_date  =  fields.Datetime(default = datetime.now())
	exp_dat_show = fields.Boolean('Is Expiry Date')
	expiry_date  = fields.Datetime("Expiry Date")
	max_amount = fields.Float("Maximum amount")
	partner_true = fields.Boolean('Allow for Specific Customer')
	partner_id  =  fields.Many2one('res.partner')
	sale_order_ids = fields.One2many('sale.order','sale_coupon_id')
	active = fields.Boolean('Active',default=True)
	amount  =  fields.Float('Coupon Amount')
	amount_type = fields.Selection([('fix','Fixed'),('per','%')],default='fix')
	description  =  fields.Text('Note')
	used = fields.Boolean('Used')   
	coupon_apply_times = fields.Integer('Coupon Code Apply Limit', default=1)
	coupon_count = fields.Integer('Coupon used count', default=0)
	coupon_desc = fields.Text('Discription')
	voucher_sent = fields.Boolean(string='Sent', readonly=True, default=False)
	product_ids = fields.Many2many('product.template',string='Products')
	product_categ_ids = fields.Many2many('product.category',string="Product Category")
	
	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: