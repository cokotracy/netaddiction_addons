# -*- coding: utf-8 -*-
from openerp import models, fields, api
import math
import re


class EbayProducts(models.Model):
    _inherit = 'product.product'



    on_ebay = fields.Boolean(string="Acceso su ebay", default=False)
    ebay_id = fields.Integer(string="ID eBay corrente")
    ebay_price = fields.Float(string="Modifica manuale prezzo eBay", default=0.0)
    set_ebay_price = fields.Boolean(string="Imponi prezzo su ebay", default=False)
    ebay_category_id = fields.Integer(string="ID categoria eBay")
    ebay_published_date = fields.Datetime(string="Data pubblicazione eBay")
    ebay_expiration_date = fields.Datetime(string="Data scadenza inserzione")
    ebay_selled = fields.Integer(string="Venduti su eBay", default=0)
    ebay_image_url = fields.Char(string="Immagini eBay")

    @api.one
    def toggle_ebay(self):
        self.on_ebay = not self.on_ebay

    def _ebay_price(self):
        """ calcola il prezzo per ebay"""

        if self.set_ebay_price and self.ebay_price >0.0:
            return self.ebay_price

        curr_price = 0.0
        if self.offer_price > 0.0:
            curr_price = self.offer_price
        elif self.special_price > 0.0:
            curr_price = self.special_price
        else:
            curr_price = self.final_price

        gadget_category = self.env["product.category"].search([("name","=","Gadget")])
        if gadget_category and self.categ_id != gadget_category.id:
            curr_price +=  (curr_price / 100.0 ) * 10.0

        curr_price, decimal = math.modf(curr_price)
        curr_price += 0.9

        return curr_price

    def _ebay_ean(self):
        """calcola l'EAN per ebay"""
        ret = re.sub("[^0-9]", "", self.barcode)
        if len(ret) < 13:
            ret = ("0" * (13-len(ret))) + ret
        return ret


    

    
