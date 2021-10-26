# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from odoo import models


class NetaddictionWebsitePreorder(models.TransientModel):
    _name = "netaddiction.website.preorder"

    def cron_product_preorder_toggle(self):
        products = self.env["product.product"].search(
            [("out_date", "<=", date.today()), ("inventory_availability", "!=", "always")]
        )
        products.inventory_availability = "always"
