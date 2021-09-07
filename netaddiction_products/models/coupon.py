# Copyright 2021-TODAY Rapsodoo (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class CouponProgram(models.Model):

    _inherit = 'coupon.program'

    def _get_program_from_products(self, products):
        '''
            Function used on products to get all the programs where a
            product is envolved
        '''
        data = {}
        if not products:
            return data
        # Get only programs with a valid domain for products
        programs_domain = [('rule_products_domain', '!=', False)]
        # Function can be used for a specific program:
        #
        #   ```
        #   programs = self.env['coupon.program'].search(YOUR_PROGRAMS_DOMAIN)
        #   products = self.env['product.product'].search(YOUR_PRODUCTS:DOMAIN)
        #   result = programs._get_program_from_products(products)
        #   ```
        #
        # or can be called for all the programs where products are envolved:
        #
        #   ```
        #   programs = self.env['coupon.program']
        #   products = self.env['product.product'].search(YOUR_PRODUCTS:DOMAIN)
        #   result = programs._get_program_from_products(products)
        #   ```
        #
        # The result is a dict composed by products as keys and programs
        # where the product is in as values. F.E.:
        #
        #   ```
        #   {
        #       product.product(458874,): coupon.program(3, 1, 2),
        #       product.product(458963,): coupon.program(1, 2),
        #   }
        #   ```
        if self:
            programs = self.filtered_domain(programs_domain)
        else:
            programs = self.search(programs_domain)
        if not programs:
            return data
        program_model = self.env['coupon.program']
        for program in programs:
            valid_products = program._get_valid_products(products)
            if not valid_products:
                continue
            for product in products:
                if product in valid_products:
                    if product not in data:
                        data[product] = program_model
                    data[product] |= program
        return data
