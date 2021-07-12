# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools.translate import html_translate
    
class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_description = fields.Html('Description for the Variant of the Product', sanitize_attributes=False, translate=html_translate)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: