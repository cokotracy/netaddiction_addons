# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import uuid
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo import http, tools, _
from odoo.http import request
from odoo.exceptions import Warning
from odoo import SUPERUSER_ID, tools
import datetime as dt
from datetime import datetime, timedelta
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

class sale_order(models.Model):
	_inherit = "sale.order"

	def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
		""" Add or set product quantity, add_qty can be negative """
		self.ensure_one()
		self = self.with_context(is_cart_update=True)
		product_context = dict(self.env.context)
		product_context.setdefault('lang', self.sudo().partner_id.lang)
		SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
		# change lang to get correct name of attributes/values
		product_with_context = self.env['product.product'].with_context(product_context)
		product = product_with_context.browse(int(product_id))

		try:
			if add_qty:
				add_qty = float(add_qty)
		except ValueError:
			add_qty = 1
		try:
			if set_qty:
				set_qty = float(set_qty)
		except ValueError:
			set_qty = 0
		quantity = 0
		order_line = False
		if self.state != 'draft':
			request.session['sale_order_id'] = None
			raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
		if line_id is not False:
			order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]

		# Create line if no line with product_id can be located
		if not order_line:
			if not product:
				raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

			no_variant_attribute_values = kwargs.get('no_variant_attribute_values') or []
			received_no_variant_values = product.env['product.template.attribute.value'].browse([int(ptav['value']) for ptav in no_variant_attribute_values])
			received_combination = product.product_template_attribute_value_ids | received_no_variant_values
			product_template = product.product_tmpl_id

			# handle all cases where incorrect or incomplete data are received
			combination = product_template._get_closest_possible_combination(received_combination)

			# get or create (if dynamic) the correct variant
			product = product_template._create_product_variant(combination)

			if not product:
				raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

			product_id = product.id

			values = self._website_product_id_change(self.id, product_id, qty=1)

			# add no_variant attributes that were not received
			for ptav in combination.filtered(lambda ptav: ptav.attribute_id.create_variant == 'no_variant' and ptav not in received_no_variant_values):
				no_variant_attribute_values.append({
					'value': ptav.id,
				})

			# save no_variant attributes values
			if no_variant_attribute_values:
				values['product_no_variant_attribute_value_ids'] = [
					(6, 0, [int(attribute['value']) for attribute in no_variant_attribute_values])
				]

			# add is_custom attribute values that were not received
			custom_values = kwargs.get('product_custom_attribute_values') or []
			received_custom_values = product.env['product.template.attribute.value'].browse([int(ptav['custom_product_template_attribute_value_id']) for ptav in custom_values])

			for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
				custom_values.append({
					'custom_product_template_attribute_value_id': ptav.id,
					'custom_value': '',
				})

			# save is_custom attributes values
			if custom_values:
				values['product_custom_attribute_value_ids'] = [(0, 0, {
					'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
					'custom_value': custom_value['custom_value']
				}) for custom_value in custom_values]

			# create the line
			order_line = SaleOrderLineSudo.create(values)

			try:
				order_line._compute_tax_id()
			except ValidationError as e:
				# The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
				_logger.debug("ValidationError occurs during tax compute. %s" % (e))
			if add_qty:
				add_qty -= 1

		# compute new quantity
		if set_qty:
			quantity = set_qty
		elif add_qty is not None:
			quantity = order_line.product_uom_qty + (add_qty or 0)

		# Remove zero of negative lines
		if quantity <= 0:
			linked_line = order_line.linked_line_id
			order_line.unlink()
			if linked_line:
				# update description of the parent
				linked_product = product_with_context.browse(linked_line.product_id.id)
				linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
		else:
			#Updating Discount based on percentage
			order = self.env['sale.order'].browse(order_line.order_id.id)

			
			# update line
			no_variant_attributes_price_extra = [ptav.price_extra for ptav in order_line.product_no_variant_attribute_value_ids]
			values = self.with_context(no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra))._website_product_id_change(self.id, product_id, qty=quantity)
			if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
				order = self.sudo().browse(self.id)
				product_context.update({
					'partner': order.partner_id,
					'quantity': quantity,
					'date': order.date_order,
					'pricelist': order.pricelist_id.id,
				})
				product = self.env['product.product'].with_context(product_context).browse(product_id)
				prod = None
				if order.sale_coupon_id:
					prod = order.sale_coupon_id.product_id
					if prod.id == product_id:
						if order.voucher_code:
							c_val = False
							by_name = request.env['web.gift.coupon'].search([('name','=ilike', order.voucher_code)])
							by_code = request.env['web.gift.coupon'].search([('c_barcode','=', order.voucher_code)])
							
							if by_name:
								c_val = by_name

							if by_code:
								c_val = by_code
							
							if c_val.amount and c_val.amount_type:
								if c_val.amount_type == 'fix':
									values['price_unit'] = -c_val.amount

								elif c_val.amount_type == 'per':
									total = 0
									for i in order.order_line:
										if i.discount_line == False:
											total += i.price_subtotal
									values['price_unit'] = -((total * c_val.amount)/100)        
					else:
						values['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
							order_line._get_display_price(product),
							order_line.product_id.taxes_id,
							order_line.tax_id,
							self.company_id
						)

			order_line.write(values)


			# link a product to the sales order
			if kwargs.get('linked_line_id'):
				linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
				order_line.write({
					'linked_line_id': linked_line.id,
				})
				linked_product = product_with_context.browse(linked_line.product_id.id)
				linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
			# Generate the description with everything. This is done after
			# creating because the following related fields have to be set:
			# - product_no_variant_attribute_value_ids
			# - product_custom_attribute_value_ids
			# - linked_line_id
			if order_line.name:
				order_line.name = order_line.name
			else:
				order_line.name = order_line.get_sale_order_line_multiline_description_sale(product)
				
		total_price = 0.0

		c_val = False
		by_name = request.env['web.gift.coupon'].search([('name','=ilike', self.voucher_code)])
		by_code = request.env['web.gift.coupon'].search([('c_barcode','=', self.voucher_code)])
		
		if by_name:
			c_val = by_name
		if by_code:
			c_val = by_code

		for line in self.order_line.filtered(lambda x: not x.discount_line):
			total_price += line.price_unit * line.product_uom_qty
		count = 0
		for line in self.order_line.filtered(lambda x: x.discount_line):
			if line.discount_line:
				if self.sale_coupon_id.amount_type == 'per':
					discount_percent = c_val.amount / 100
					old_discount = line.price_unit

					new_discount = (total_price*discount_percent)

					if new_discount > self.sale_coupon_id.max_amount:
						new_discount = self.sale_coupon_id.max_amount
					if new_discount and not order_line.redeem_points:
						line.write({
							'price_unit' : -new_discount
						})

					if line.price_unit == 0.00:
						line.unlink()
				if c_val:
					if self.sale_coupon_id.amount_type == 'per':
						discount_percent = c_val.amount / 100
						old_discount = line.price_unit
						new_discount = (total_price*discount_percent)
					else:
						new_discount = c_val.amount
					if new_discount and order_line.redeem_points:
						if count == 0:
							line.write({
								'price_unit' : -order_line.redeem_points * order_line.order_id.redeem_value
							})
						else:
							line.write({
							'price_unit' : - new_discount
							})
						count = count+1
				else:
					new_discount = False
				if order_line.redeem_points and not new_discount:
					line.write({
					'price_unit' : - order_line.redeem_points * order_line.order_id.redeem_value
					})

		option_lines = self.order_line.filtered(lambda l: l.linked_line_id.id == order_line.id)

		return {'line_id': order_line.id, 'quantity': quantity, 'option_ids': list(set(option_lines.ids))}  

	def assign_voucher_code(self, code):
		self.ensure_one()
		self.update({
			'voucher_code' : code
			})
		return
	
	voucher_code = fields.Char(string='Voucher Code', readonly=True)
	sale_coupon_id = fields.Many2one('web.gift.coupon',"Coupon Id")

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	discount_line = fields.Boolean(string='Discount line',readonly=True)
	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
