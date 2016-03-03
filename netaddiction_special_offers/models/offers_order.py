# -*- coding: utf-8 -*-
from openerp import models, fields, api

class OfferOrder(models.Model):
    _inherit = 'sale.order'

    offers_cart = fields.Many2one('netaddiction.specialoffer.offer_cart_line', string='offerte carrello attive')

    @api.one
    def action_problems(self):
    	for line in self.order_line:
    		if( line.offer_type and self.state == 'draft' and not line.negate_offer ):
    		 	offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
    		 	if offer_line:
    		 		offer_line.qty_selled += line.product_uom_qty
    		 		offer_line.active = offer_line.qty_selled <= offer_line.qty_limit
#TODO aggiorna anche quantità carrelo
    	self.state = 'problem'


    @api.multi
    def action_confirm(self):
    	for order in self:
    		for line in self.order_line:
    			if( line.offer_type and self.state == 'draft' and not line.negate_offer ):
    		 		offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
    		 		if offer_line:
    		 			offer_line.qty_selled += line.product_uom_qty
    		 			offer_line.active = offer_line.qty_selled <= offer_line.qty_limit
    	#TODO se c'è un commento spostare in problem non in sale
      #TODO aggiorna anche quantità carrelo  #
        super(OfferOrder, self).action_confirm()
    
    @api.multi
    def action_cancel(self):
        self._send_cancel_mail()
        for order in self:
        	for line in self.order_line:
        		if( line.offer_type and self.state != 'draft' and not line.negate_offer):
        			offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
    		 	if offer_line:
    		 		offer_line.qty_selled -= line.product_uom_qty
                    #TODO aggiorna anche quantità carrelo
        super(OfferOrder, self).action_cancel()



    #comportamento su offerte spente: vanno riattivate sempre manualmente
    @api.one
    def extract_cart_offers(self):
        """Metodo per controllare se ci sono offerte carrello attive sui prodotti nell'ordine.
            Ritorna la lista delle offerte ordinata per priorità
        """

       #  #creo la lista degli id prodotto e delle offerte carrello
       #  product_order_list = []
       #  offers_set = set()
       #  for ol in self.order_line:
       #      i = 0
       #      if len(ol.product_id.offer_cart_lines) > 0:
       #          offers_set.add(ol.product_id.offer_cart_lines[0].offer_cart_id)

       #      while i < ol.product_uom_qty:
       #          #aggiungo i prodotti considerando la product_uom_qty
       #          product_order_list.append(ol.product_id)
       #          i +=1
       #  offers_list = list(offers_set)
       #  offers_list.sort(key=lambda offer: offer.priority)
       # # return offers_list
       # # --------
       #  offer_dict = {}
       #  #creo un dizionario offerta carrello -> lista prodotti
       #  for offer in offers_list:
       #      prod_list = []
       #      for prod_line in offer.products_list:
       #          prod_list.append(prod_line.product_id.id)
       #      offer_dict[offer] = prod_list

       #  print offer_dict
       #  for offer in offers_list:
       #      temp_list = []
       #      for product in product_order_list:
       #          if product.id in offer_dict[offer]:
       #              temp_list.append(product)
       #      self._verify_cart_offers(offer,temp_list,product_order_list)


        #----- remake ----
        #chiavi = offerte carrello che hanno una possibilità di essere applicate a questo ordine
        #valori = lista di (order_line)
        offer_dict = {} 
        #lista ordinata per priorità di offerte carrello che hanno una possibilità di essere applicate a questo ordine
        offer_list = []
        for ol in self.order_line:
           
            if len(ol.product_id.offer_cart_lines) > 0:
                offer = ol.product_id.offer_cart_lines[0].offer_cart_id
                if offer not in offer_dict:
                    prod_list =[]
                    prod_list.append(ol)
                    offer_dict[offer] = prod_list
                else:
                    offer_dict[offer].append(ol)

        print "OFFER DICT:"
        print offer_dict 
        print "----------"
        offer_list = offer_dict.keys()
        offer_list.sort(key=lambda offer: offer.priority)
        order_lines = [o for o in self.order_line]
        
        print "OFFER LIST:"
        print offer_list
        print "----------"

        print "OFFER LINES:"
        print order_lines
        print "----------"

#controllo scadenze offerta
        #for offer in offer_list:
            #self._verify_cart_offers(offer,offer_dict[offer])


    @api.one
    def _verify_cart_offers(self,offer,order_lines):
        if(offer.date_end > fields.Datetime.now()):
            if(offer.offer_type == 1):
                #bundle
                pass
                
            elif(offer.offer_type == 2):
               #nxm
               self._apply_n_x_m(offer,order_lines)

            elif (offer.offer_type == 3):
                #nxprezzo
                #if len(selected_prod) >= offer.n
                pass
       
    @api.one
    def _apply_n_x_m(self,offer,order_lines):
        tot_qty = 0
        for ol in order_lines:
            tot_qty += ol.product_uom_qty

        if tot_qty >= offer.n and offer.n > 0:
            part = tot_qty//offer.n
            num_prod_for_free = part * (offer.n - offer.m)
            i = 0
            #order lines non prodotti
            order_line.sort(key=lambda ol: ol.price_unit)
            while i < num_prod_for_free:
                ol = order_lines[i] if order_lines[i] else None
                if(ol and ol.product_uom_qty <= num_prod_for_free - i):
                    offer_line = ol.product_id.offer_cart_lines[0]
                    if (offer_line.qty_max_buyable > 0 and ol.product_uom_qty > offer_line.qty_max_buyable):
                            raise QtyMaxBuyableException(ol.product_id.name)
                    else:
                        ol.price_unit = 0.0
                        i += ol.product_uom_qty
                        
                else:
                    self._split_order_line(ol,num_prod_for_free -i,ol.product_uom_qty - (num_prod_for_free -i))
                    ol.price_unit = 0.0
                    #spezza le linee

                    i = num_prod_for_free
            for ol in order_lines:
                self.offers_cart = [(4, ol.product_id.offer_cart_lines[0], _)]

    @api.one
    def _split_order_line(self,order_line,qty_1,qty_2):
        """splitta una order line in due diverse order line (sempre dentro lo stesso ordine) rispettivamente di quantità qty_1 e qty_2
            per fare ciò assegna qty_1 alla quantità di order_linee ne crea una nuova con quantità qty_2
            ritorna None se qty_1 + qty_2 != order_line.product_uom_qty, altimenti un riferimento alla nuova order_line
        """
        if qty_1 + qty_2 != order_line.product_uom_qty:
            return None
        else:
            order_line.product_uom_qty = qty_1
            order_line.product_uom_change()
            return self.env['sale.order.line'].create({'product_id':order_line.product_id, 'order_id' : self.id, 'product_uom_qty' : qty_2})


            




        
