# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Pricelist(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(selection=(
            ('list_price', 'Prezzo di vendita'), 
            ('standard_price', 'Costo'), 
            ('pricelist', 'Altra Price List')
            ), string="Basato su", required=True)

class product_pricelist(models.Model):

    _inherit = "product.pricelist"

    expression = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')

    carrier_id = fields.Many2one(comodel_name="delivery.carrier", string="Metodo di Spedizione")
    carrier_price = fields.Float(string="Costo Spedizione")
    carrier_gratis = fields.Float(string="Spedizione Gratis se valore maggiore di",default="0.00")
    

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
            
            #tassa = obj.taxes_id.amount
#
            #if tassa:
            #    detax = obj.offer_price / (float(1) + float(tassa/100))
            #else:
            #    detax = obj.offer_price
#
            #offer_detax = round(detax,2)
            
            real_price = obj.offer_price if (obj.offer_price >0 and obj.offer_price < price) else price

            results[pid] = (real_price,other_val)

        return results

    @api.one
    def populate_item_ids_from_expression(self):
        if self.expression:
            dom = self.expression.find_products_domain()
            ids = []
        else:
            raise ValidationError("Se non metti un'espressione non posso aggiungere prodotti")

        for prod in self.env['product.product'].search(dom):
            attr = {
                'applied_on' : '0_product_variant',
                'product_id' : prod.id,
                'compute_price' : 'formula',
                'base' : 'list_price',
                'price_discount' : 20,
                'pricelist_id' : self.id
            }
            self.env['product.pricelist.item'].create(attr)
