# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo import http, SUPERUSER_ID, tools, _
from odoo.http import request

class GiftWrapConfiguration(models.Model):
	_name = 'giftwrap.configuration'
	_rec_name = 'product_id'
				
	product_id  = fields.Many2one('product.product','Product', domain = [('type', '=', 'service')])
	price  =  fields.Float('Price')

	@api.onchange('product_id')
	def _onchange_giftwrap(self):
		if self.product_id:
			self.update({
				'price': self.product_id.list_price,
			})

class websiteInherit(models.Model):
	_inherit = 'website'

	def get_website_giftwrap(self):  
		giftwrap_ids=self.env['giftwrap.configuration'].sudo().search([])
		return giftwrap_ids  

	def get_gift_product(self):
		giftwrap = self.env['giftwrap.configuration'].sudo().browse(self.id)
		return giftwrap  

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
