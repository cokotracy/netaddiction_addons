# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, time
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    net_sales_count = fields.Float(compute='_compute_net_sales_count', string='Sold QTY', store=True)

    def _compute_net_sales_count(self):
        for product in self:
            if not product.id:
                product.net_sales_count = 0.0
                continue
            product.net_sales_count = product.sales_count

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	est_date_addon = fields.Integer('Estimate date Addon',default= 5)
