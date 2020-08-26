# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models


class netaddictionWebsite(models.Model):
    _inherit = 'website'

    def website_product_category(self):
        ProductCategory = self.env['product.public.category']
        domain = [('parent_id', '=', False)] + self.website_domain()
        return ProductCategory.search(domain)

        