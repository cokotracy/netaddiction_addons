# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class ProductPack(models.Model):
	_name = 'product.pack'
	_description = "Product Pack"
	
	product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
	qty_uom = fields.Float(string='Quantity', required=True, defaults=1.0)
	bi_product_template = fields.Many2one(comodel_name='product.template', string='Product pack')
	bi_image = fields.Binary(related='product_id.image_1920', string='Image', store=True)
	price = fields.Float(related='product_id.lst_price', string='Product Price')
	uom_id = fields.Many2one(related='product_id.uom_id' , string="Unit of Measure", readonly="1")
	name = fields.Char(related='product_id.name', readonly="1")

class ProductProduct(models.Model):
	_inherit = 'product.template'

	is_pack = fields.Boolean(string='Is Product Pack')
	cal_pack_price = fields.Boolean(string='Calculate Pack Price')
	pack_ids = fields.One2many(comodel_name='product.pack', inverse_name='bi_product_template', string='Product pack')

	@api.model
	def create(self,vals):
		total = 0
		res = super(ProductProduct,self).create(vals)
		if res.cal_pack_price:
			if 'pack_ids' in vals or 'cal_pack_price' in vals:
					for pack_product in res.pack_ids:
							qty = pack_product.qty_uom
							price = pack_product.product_id.list_price
							total += qty * price
		if total > 0:
			res.list_price = total
		return res


	def write(self,vals):
		total = 0
		res = super(ProductProduct, self).write(vals)
		for pk in self:
			if pk.cal_pack_price:
				if 'pack_ids' in vals or 'cal_pack_price' in vals:
					for pack_product in pk.pack_ids:
						qty = pack_product.qty_uom
						price = pack_product.product_id.list_price
						total += qty * price

		if total > 0:
			self.list_price = total
		return res

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'		

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_bundle = fields.Boolean('Allow Manual Dropshipping Delivery')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        allow_bundle = self.env['ir.config_parameter'].sudo().get_param('product_bundle_pack.allow_bundle')
        res.update(
            allow_bundle = allow_bundle,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('product_bundle_pack.allow_bundle', self.allow_bundle)