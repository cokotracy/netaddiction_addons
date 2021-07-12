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
    

    @api.model
    def create(self,vals):
        brand = super(ProductBrand, self).create(vals)
        if vals.get('brand_id'):
            brand_brw = self.env['product.brand'].browse(vals.get('brand_id'))
            brand_brw.write({'product_ids': [(4, brand.id)]})
        return brand
    

    def write(self,value):
        brand = super(ProductBrand, self).write(value)
        if value.get('brand_id'):
            brand_brw = self.env['product.brand'].browse(value.get('brand_id'))
            brand_brw.write({'product_ids': [(4, self.id)]})
            products = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
            product_ids = self.env['product.template'].search([('brand_id','=',brand_brw.id)])
            brand_ids = self.env['product.brand'].search([])
            for brand in brand_ids:
                for product_id in brand.product_ids:
                    if product_id in product_ids and product_id.brand_id != brand:
                        brand.write({
                            'product_ids': [(3, product_id.id)]
                        })
            for product_variants in products:
                product_variants.update({'brand_id': self.brand_id.id})
        return brand


    def _create_variant_ids(self):
        self.flush()
        Product = self.env["product.product"]

        variants_to_create = []
        variants_to_activate = Product
        variants_to_unlink = Product

        for tmpl_id in self:
            lines_without_no_variants = tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes()

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted('active')

            current_variants_to_create = []
            current_variants_to_activate = Product

            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            single_value_lines = lines_without_no_variants.filtered(lambda ptal: len(ptal.product_template_value_ids._only_active()) == 1)
            if single_value_lines:
                for variant in all_variants:
                    combination = variant.product_template_attribute_value_ids | single_value_lines.product_template_value_ids._only_active()
                    # Do not add single value if the resulting combination would
                    # be invalid anyway.
                    if (
                        len(combination) == len(lines_without_no_variants) and
                        combination.attribute_line_id == lines_without_no_variants
                    ):
                        variant.product_template_attribute_value_ids = combination

            # Determine which product variants need to be created based on the attribute
            # configuration. If any attribute is set to generate variants dynamically, skip the
            # process.
            # Technical note: if there is no attribute, a variant is still created because
            # 'not any([])' and 'set([]) not in set([])' are True.
            if not tmpl_id.has_dynamic_attributes():
                # Iterator containing all possible `product.template.attribute.value` combination
                # The iterator is used to avoid MemoryError in case of a huge number of combination.
                all_combinations = itertools.product(*[
                    ptal.product_template_value_ids._only_active() for ptal in lines_without_no_variants
                ])
                # Set containing existing `product.template.attribute.value` combination
                existing_variants = {
                    variant.product_template_attribute_value_ids: variant for variant in all_variants
                }
                # For each possible variant, create if it doesn't exist yet.
                for combination_tuple in all_combinations:
                    combination = self.env['product.template.attribute.value'].concat(*combination_tuple)
                    if combination in existing_variants:
                        current_variants_to_activate += existing_variants[combination]
                    else:
                        current_variants_to_create.append({
                            'product_tmpl_id': tmpl_id.id,
                            'product_template_attribute_value_ids': [(6, 0, combination.ids)],
                            'active': tmpl_id.active,
                            'brand_id':tmpl_id.brand_id.id,
                        })
                        if len(current_variants_to_create) > 1000:
                            raise UserError(_(
                                'The number of variants to generate is too high. '
                                'You should either not generate variants for each combination or generate them on demand from the sales order. '
                                'To do so, open the form view of attributes and change the mode of *Create Variants*.'))
                variants_to_create += current_variants_to_create
                variants_to_activate += current_variants_to_activate

            variants_to_unlink += all_variants - current_variants_to_activate

        if variants_to_activate:
            variants_to_activate.write({'active': True})
        if variants_to_create:
            Product.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink._unlink_or_archive()

        # prefetched o2m have to be reloaded (because of active_test)
        # (eg. product.template: product_variant_ids)
        # We can't rely on existing invalidate_cache because of the savepoint
        # in _unlink_or_archive.
        self.flush()
        self.invalidate_cache()
        return True


class product_product(models.Model):
    _inherit = 'product.product'
	
    brand_id = fields.Many2one('product.brand', 'Brand')
    
       

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
