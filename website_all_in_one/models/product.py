# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _ ,tools
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
import psycopg2
import itertools
from odoo.exceptions import ValidationError, except_orm

class ProductBrand(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', 'Brand')
    
    def create_variant_ids(self):
        Product = self.env["product.product"]
        for tmpl_id in self.with_context(active_test=False):
			# adding an attribute with only one value should not recreate product
			# write this attribute on every product to make sure we don't lose them
            variant_alone = tmpl_id.attribute_line_ids.filtered(lambda line: len(line.value_ids) == 1).mapped('value_ids')
            for value_id in variant_alone:
                updated_products = tmpl_id.product_variant_ids.filtered(lambda product: value_id.attribute_id not in product.mapped('attribute_value_ids.attribute_id'))
                updated_products.write({'attribute_value_ids': [(4, value_id.id)],
					'brand_id':tmpl_id.brand_id.id,
					
					
				})
			# list of values combination
            existing_variants = [set(variant.attribute_value_ids.ids) for variant in tmpl_id.product_variant_ids]
            variant_matrix = itertools.product(*(line.value_ids for line in tmpl_id.attribute_line_ids if line.value_ids and line.value_ids[0].attribute_id.create_variant))
            variant_matrix = map(lambda record_list: reduce(lambda x, y: x + y, record_list, self.env['product.attribute.value']), variant_matrix)
            to_create_variants = filter(lambda rec_set: set(rec_set.ids) not in existing_variants, variant_matrix)

			# check product
            variants_to_activate = self.env['product.product']
            variants_to_unlink = self.env['product.product']
            for product_id in tmpl_id.product_variant_ids:
                if not product_id.active and product_id.attribute_value_ids in variant_matrix:
                    variants_to_activate |= product_id
                elif product_id.attribute_value_ids not in variant_matrix:
                    variants_to_unlink |= product_id
            if variants_to_activate:
                variants_to_activate.write({'active': True})

			# create new product
            for variant_ids in to_create_variants:
                new_variant = Product.create({
					'product_tmpl_id': tmpl_id.id,
					'attribute_value_ids': [(6, 0, variant_ids.ids)],
					'brand_id':tmpl_id.brand_id.id,
									
					
				})

			
			# unlink or inactive product
            for variant in variants_to_unlink:
                try:
                    with self._cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                        variant.unlink()
				# We catch all kind of exception to be sure that the operation doesn't fail.
                except (psycopg2.Error, except_orm):
                    variant.write({'active': False})
                    pass
        return True



class product_product(models.Model):
    _inherit = 'product.product'
	
    brand_id = fields.Many2one('product.brand', 'Brand')
    

class website(models.Model):
    _inherit = 'website'

    def get_product_brand(self):  
        prod_ids=self.env['product.brand'].search([])
        return prod_ids   
       
    def get_product_category(self):  
        category_ids=self.env['product.public.category'].search( [('parent_id', '=', False)] )
        return category_ids       
    

            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
