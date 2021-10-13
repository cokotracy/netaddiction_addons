# Copyright 2021 Rapsodoo (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ManageProductSeller(models.TransientModel):

    _name = 'manage.product.seller'
    _description = 'Manage sellers from product to write them on template'

    def default_seller_ids(self):
        product = self.env['product.product'].browse(
            self.env.context.get('na_product_id'))
        sellers = product._get_product_seller_ids()
        return sellers

    seller_ids = fields.Many2many(
        'product.supplierinfo',
        default=default_seller_ids,
        string='Details',
    )
