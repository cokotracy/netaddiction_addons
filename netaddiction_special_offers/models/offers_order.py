# -*- coding: utf-8 -*-
from openerp import models, fields, api

class OfferOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def action_problems(self):
    	for line in self.order_line:
    		if( line.offer_price_unit and self.state == 'draft' and not line.negate_offer ):
    		 	offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
    		 	if offer_line:
    		 		offer_line.qty_selled += line.product_uom_qty
    		 		offer_line.active = offer_line.qty_selled <= offer_line.qty_limit

    	self.state = 'problem'


    @api.multi
    def action_confirm(self):
    	for order in self:
    		for line in self.order_line:
    			if( line.offer_price_unit and self.state == 'draft' and not line.negate_offer ):
    		 		offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
    		 		if offer_line:
    		 			offer_line.qty_selled += line.product_uom_qty
    		 			offer_line.active = offer_line.qty_selled <= offer_line.qty_limit
    	#TODO se c'è un commento spostare in problem non in sale
        super(OfferOrder, self).action_confirm()
    
    @api.multi
    def action_cancel(self):
        self._send_cancel_mail()
        for order in self:
        	for line in self.order_line:
        		if( line.offer_price_unit and self.state != 'draft' and not line.negate_offer):
        			offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
    		 	if offer_line:
    		 		offer_line.qty_selled -= line.product_uom_qty
        super(OfferOrder, self).action_cancel()



   #comportamento su offerte spente: vanno riattivate sempre manualmente
    @api.one
    def process_cart_offers(self):

        #creo la lista degli id prodotto e delle offerte carrello
        product_order_list = []
        offers_set = set()
        for ol in self.order_line:
            i = 0
           # print "product %s offer catalog lenght %s" %(ol.product_id,len(ol.product_id.offer_cart_lines))
            if len(ol.product_id.offer_cart_lines) > 0:
                offers_set.add(ol.product_id.offer_cart_lines[0].offer_cart_id)

            while i < ol.product_uom_qty:
                product_order_list.append(ol.product_id.id)
                i +=1
        offers_list = list(offers_set)
        offers_list.sort(key=lambda offer: offer.priority)

        print "product list %s" % product_order_list
        print "offer set %s" % offers_set
        print "offer list %s" % offers_list





        
