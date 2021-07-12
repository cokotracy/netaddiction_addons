# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class website(models.Model):
	_inherit = 'website'

	def get_dynamic_count(self,prods):
		filters = self.env['product.filter.value'].sudo().search([])
		for fltr in filters:
			count = 0
			for product in prods:
				for flt in product.filter_ids:
					if fltr in flt.filter_value_ids:
						count += 1
			fltr.sudo().write({
				'dynamic_count' : count,
			})

class FilterProductTemplate(models.Model):
	_inherit = 'product.template'

	filter_ids = fields.One2many('filter.product.line','product_tmpl_id','Product Filter')


class ProductFilters(models.Model):
	_name = 'product.filter'
	_description = 'Filter Product'
	_order = 'group_id'

	name = fields.Char('Name')
	type = fields.Selection([
		('radio', 'Radio'),
		('select', 'Select'),
		('color', 'Color')], default='radio', required=True)
	group_id = fields.Many2one('group.filter','Group Filter',required=True,default=lambda self: self.env['group.filter'].search([('name','=','Other Filters')],limit=1))
	filter_value_ids = fields.One2many('product.filter.value','filter_id',string="Filter Values",)
	filter_ids = fields.One2many('filter.product.line','filter_name_id','Product Filter')


class FilterProductValue(models.Model):
	_name = 'product.filter.value' 
	_description = 'Filter Product Value'

	@api.depends('filter_id','name','html_color')
	def _attribute_count(self):
		for filters in self:
			product_obj = self.env['product.template']
			product_ids = product_obj.search([])
			count = 0
			if product_ids:
				for product in product_ids:
					if product.filter_ids:
						for flt in product.filter_ids:
							if filters in flt.filter_value_ids:
								count += 1
			filters.product_count = count

	name = fields.Char('Filter Values Name')
	filter_id = fields.Many2one('product.filter','Filter Name')
	
	html_color = fields.Char(
		string='HTML Color Index', oldname='color',
		help="""Here you can set a
		specific HTML color index (e.g. #ff0000) to display the color if the
		filterer type is 'Color'.""")
	product_count = fields.Integer('Count',compute='_attribute_count',)
	dynamic_count = fields.Integer("Dynamic Count")
	

class FilterProductGroup(models.Model):
	_name = 'group.filter'
	_description = 'Filter Group'

	name = fields.Char('Filter Group Name')


class FilterProductLine(models.Model):
	_name = 'filter.product.line'
	_description = 'Filter Product'

	product_tmpl_id = fields.Many2one('product.template','Filter View')
	filter_name_id = fields.Many2one('product.filter','Filter Name')
	filter_value_ids = fields.Many2many('product.filter.value',string="Filter Values")


	@api.onchange('filter_name_id')
	def onchange_filter_name_id(self):
		for flt in self:
			if flt.filter_name_id:
				if flt.filter_name_id != flt.filter_value_ids.filter_id :
					# reset task when changing project
					flt.filter_value_ids = False
				return {'domain': {
					'filter_value_ids': [('filter_id', '=', flt.filter_name_id.id)]
				}}


	@api.model
	def create(self,vals):
		res = super(FilterProductLine, self).create(vals)
		if 'filter_value_ids' in vals:
			for value in res.filter_value_ids:
				value._attribute_count()
		return res

	def write(self,vals):
		if 'filter_value_ids' in vals:
			for value in vals['filter_value_ids']:
				for flt_value in value[2]:
					flt = self.env['product.filter.value'].browse(flt_value)
					flt._attribute_count()
			for value in self.filter_value_ids:
				value._attribute_count()
		return super(FilterProductLine, self).write(vals)
