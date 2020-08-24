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

    def _get_netaddiction_combination_info(self, website, combination_info):
        netaddiction_combination_info = combination_info
        FieldMonetary = self.env['ir.qweb.field.monetary']
        monetary_options = {
            'display_currency': website.get_current_pricelist().currency_id,
        }
        list_price = FieldMonetary.value_to_html(combination_info['list_price'], monetary_options).split('.')
        list_price_decimal = u'</span><span class="o_netaddiction_decimal">.' + list_price[1]
        netaddiction_combination_info['netaddiction_list_price'] = list_price[0] + list_price_decimal

        price_formate = FieldMonetary.value_to_html(combination_info['price'], monetary_options).split('.')
        decimal = u'</span><span class="o_netaddiction_decimal">.' + price_formate[1]
        netaddiction_combination_info['netaddiction_price'] = price_formate[0] + decimal
        return netaddiction_combination_info

