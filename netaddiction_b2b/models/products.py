# -*- coding: utf-8 -*-

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

class Products(models.Model):
    _inherit = 'product.product'

    final_price_deiva = fields.Float(string="Prezzo Listino Deivato", digits_compute= dp.get_precision('Product Price'), compute="_get_final_price_deiva")

    @api.depends('final_price')
    def _get_final_price_deiva(self):
    	for p in self:
            tassa = p.taxes_id.amount

            price = p.final_price

            if tassa:
                detax = price / (float(1) + float(tassa/100))
            else:
                detax = price

            p.final_price_deiva = round(detax,2)