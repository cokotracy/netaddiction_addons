# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from odoo import fields, models


class NetaddictionWebsitePreorder(models.TransientModel):
    _name = "netaddiction.website.preorder"

    def cron_product_preorder_toggle(self):
        products = self.env["product.product"].search(
            [("out_date", "<=", date.today()), ("inventory_availability", "!=", "always")]
        )
        products.inventory_availability = "always"


class Website(models.Model):

    _inherit = 'website'

    def sale_get_order(self, force_create=False, code=None,
                       update_pricelist=False, force_pricelist=False):
        sale = super().sale_get_order(force_create, code,
                                      update_pricelist, force_pricelist)
        # Actually Odoo freeze the price of a product at the moment we add it
        # to the order. In netaddiction ecommerce this is wrong because
        # I can create a cart today and I can come back tommorrow to check
        # my cart. In this case I want to receive discount created meanwhile.
        if sale:
            sale.date_order = fields.Datetime.now()
            sale.update_prices()
        return sale
