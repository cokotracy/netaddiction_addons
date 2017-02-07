# -*- coding: utf-8 -*-
from openerp import api, fields, models


class EbayOrder(models.Model):
    _inherit = 'sale.order'

    from_ebay = fields.Boolean(string='Da Ebay', default=False)
    ebay_transaction_id = fields.Char(string="Ebay TransactionID")
    ebay_item_id = fields.Char(string="Ebay ItemID del prodotto nell'ordine")
    ebay_order_id = fields.Char(string="Ebay Order ID", default="")
    ebay_completed = fields.Boolean(string='Completato su eBay', default=False)