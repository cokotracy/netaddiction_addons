# Copyright 2021 Rapsodoo (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MassiveProductPriceChange(models.TransientModel):

    _name = 'massive.product.price.change'
    _description = 'Massive change for product price from template'

    sale_price = fields.Float()

    def apply_price(self):
        template_ids = self.env.context.get('active_ids', [])
        if not template_ids:
            return True
        products = self.env['product.product'].search(
            [('product_tmpl_id', 'in', template_ids)])
        products.lst_price = self.sale_price
        return True
