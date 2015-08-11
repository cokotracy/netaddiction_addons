# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Products_Bonus(models.Model):
    _name = 'netaddiction.product.bonus'
    _inherits = {
        'product.product' : 'bonus_product',
    }

    bonus_product = fields.Many2one('product.product',ondelete="cascade")
    type = fields.Selection((('digital', 'Digitale'),('product','Prodotto Fisico')),
        string='Product Type',required="True")
    bonus_parent_ids = fields.Many2many('product.product','product_bonus_rel',
        'op_bonus_id','op_product_id',string="Prodotti Associati",required="True")
    list_price = fields.Float(string="Prezzo di Vendita",default="0",readonly="True")

    def create(self, cr, uid, vals, context=None):
        new_id = super(Products_Bonus, self).create(cr, uid, vals, context=context)

        #product = self.env['product.product']
        return new_id



class Product(models.Model):
    _inherit="product.product"

    bonus_products = fields.Many2many('netaddiction.product.bonus','product_bonus_rel',
        'op_product_id','op_bonus_id',string="Bonus Associati")
