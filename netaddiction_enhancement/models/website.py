# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from odoo import models, fields


class NetaddictionEnhancement(models.Model):
    _name = "netaddiction.enhancement"

    def cron_product_preorder_toggle(self):
        products = self.env["product.product"].search(
            [("out_date", "<=", date.today()), ("inventory_availability", "!=", "always")]
        )
        for product in products:
            product.inventory_availability = "always"


class CategoryDescriptionInherit(models.Model):
    _inherit = "product.public.category"
    description = fields.Text(name="description")
