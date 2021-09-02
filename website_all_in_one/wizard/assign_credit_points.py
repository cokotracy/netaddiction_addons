# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, time, datetime

class CreditPoints(models.Model):
	_name = "assign.credit.points"
	_description = "assign.credit.points"

	credit_points = fields.Float('Credit Point')

	@api.model
	def default_get(self, default_fields):
		res = super(CreditPoints, self).default_get(default_fields)
		active_id = self.env.context.get('active_ids')
		reviews_ids = self.env['reviews.ratings'].browse(active_id)
		points = 0
		for review in reviews_ids:
			public_category = self.env['product.public.category'].search([('product_tmpl_ids','in',review.rating_product_id.id)])
			if public_category.loyal_for_review:
				points += public_category.loyal_for_review
			else:
				points += public_category.parent_id.loyal_for_review
		res['credit_points'] = points
		return res

	def button_assign_credit_points(self):
		active_id = self.env.context.get('active_ids')
		reviews_ids = self.env['reviews.ratings'].browse(active_id)
		for review in reviews_ids:
			if review['customer_id'] != reviews_ids[0]['customer_id']:
				raise UserError(
					_('Not all reviews are for the same user!'))
		partner_obj = self.env['res.partner'].browse(reviews_ids[0]['customer_id'].partner_id.id)
		if 'loyalty_points' in self.env['res.partner']._fields:
			partner_obj.write({'loyalty_points':self.credit_points+self.env.user.partner_id.loyalty_points})