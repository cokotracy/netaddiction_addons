# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Pricelist(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(selection=(
            ('final_price_deiva','Prezzo Listino'),
            ('list_price', 'Prezzo di vendita deivato'), 
            ('standard_price', 'Costo'), 
            ('pricelist', 'Altra Price List')
            ), string="Basato su", required=True)

class product_pricelist(models.Model):

    _inherit = "product.pricelist"

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        """
        Serve a dare il prezzo corretto alla pricelist: se l'offer_price è inferiore al prezzo dell'attuale pricelist
        allore restituisco l'offer price.
        """
        results = super(product_pricelist,self)._price_rule_get_multi(cr,uid,pricelist,products_by_qty_by_partner,context=context)
        
        for pid in results:
            price = results[pid][0]
            other_val = results[pid][1]
            
            objs = self.pool('product.product').search(cr,uid,[('id','=',int(pid))])
            obj = self.pool('product.product').browse(cr, uid, objs, context=context)
            
            tassa = obj.taxes_id.amount

            if tassa:
                detax = obj.offer_price / (float(1) + float(tassa/100))

            offer_detax = round(detax,2)
            
            real_price = obj.offer_price if (obj.offer_price >0 and obj.offer_price < price) else price

            results[pid] = (real_price,other_val)

        return results