# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models


class website(models.Model):

    _inherit = 'website'

    def get_product_category(self):
        return self.env['product.public.category'].search(
            [('parent_id', '=', False)])
