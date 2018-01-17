# -*- coding: utf-8 -*-
from openerp import models, fields, api
import math
import re


class AmazonProducts(models.Model):
    _inherit = 'product.product'

    on_amazon = fields.Boolean(string="Acceso su amazon", default=False)
    # amazon_id = '' --> convenzione per 'non hostato su amazon' 
    amazon_id = fields.Char(string="ID amazon corrente", default='')
    amazon_price = fields.Float(string="Modifica manuale prezzo amazon", default=0.0)
    set_amazon_price = fields.Boolean(string="Imponi prezzo su amazon", default=False)
    amazon_published_date = fields.Datetime(string="Data pubblicazione amazon")
    amazon_expiration_date = fields.Datetime(string="Data scadenza inserzione")
    amazon_image_expiration_date = fields.Datetime(string="Data scadenza immagine amazon")
    amazon_sold = fields.Integer(string="Venduti su amazon", default=0)
    amazon_image_url = fields.Char(string="Immagini amazon")

    @api.one
    def toggle_amazon(self):
        self.on_amazon = not self.on_amazon
        if self.on_amazon:
            self.amazon_price = self.compute_amazon_price()

    def compute_amazon_price(self):
        """ calcola il prezzo per amazon"""

        if self.set_amazon_price and self.amazon_price > 0.0:
            return self.amazon_price

        curr_price = self.offer_price if self.offer_price > 0.0 else self.list_price

        # gadget_category = self.env["product.category"].search([("name", "=", "Gadget")])
        # if gadget_category and self.categ_id.id != gadget_category.id:
        #     curr_price += (curr_price / 100.0) * 10.0

        decimal, curr_price = math.modf(curr_price)
        curr_price += 0.9

        return curr_price

    def _amazon_ean(self):
        """calcola l'EAN per amazon"""
        ret = re.sub("[^0-9]", "", self.barcode)
        if len(ret) < 13:
            ret = ("0" * (13 - len(ret))) + ret
        return ret