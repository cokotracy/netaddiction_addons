# -*- coding: utf-8 -*-
from openerp import models, fields, api

class OfferOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def action_problems(self):
    	for line in self.order_line:
    		if( line.offer_price_unit and self.state == 'draft' and not line.negate_offer ):
    		 	offer_line = self.product_id.offer_lines[0] if len(self.product_id.offer_lines) >0 else None
    		 	if offer_line:
    		 		offer_line.qty_selled += line.product_uom_qty
    		 		offer_line.active = offer_line.qty_selled <= offer_line.qty_limit

    	self.state = 'problem'


    @api.multi
    def action_confirm(self):
    	for order in self:
    		for line in self.order_line:
    			if( line.offer_price_unit and self.state == 'draft' and not line.negate_offer ):
    		 		offer_line = self.product_id.offer_lines[0] if len(self.product_id.offer_lines) >0 else None
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
        			offer_line = self.product_id.offer_lines[0] if len(self.product_id.offer_lines) >0 else None
    		 	if offer_line:
    		 		offer_line.qty_selled -= line.product_uom_qty
        super(OfferOrder, self).action_cancel()



   #comportamento su offerte spente: vanno riattivate sempre manualmente