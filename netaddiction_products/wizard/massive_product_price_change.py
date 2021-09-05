# Copyright 2021 Rapsodoo (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class MassiveProductPriceChange(models.TransientModel):
    _name = 'massive.product.price.change'
    _description = 'Massive change for product price from template'

    def default_product_ids(self):
        active_ids = self.env.context.get('active_ids', []) 
        domain =[('product_tmpl_id', 'in', active_ids)]
        return self.env['product.product'].search(domain).ids

    product_ids = fields.Many2many(
        'product.product',
        default=default_product_ids,
        string='Products',
    )
