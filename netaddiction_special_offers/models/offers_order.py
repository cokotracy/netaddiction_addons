# -*- coding: utf-8 -*-
from openerp import models, fields, api

class OfferOrder(models.Model):
    _inherit = 'sale.order'

    offers_cart = fields.One2many('netaddiction.order.specialoffer.cart.history','order_id', string='offerte carrello attive')

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
        for offer in offer_list:
            print "offer type: " 
            print offer.offer_type
            self._verify_cart_offers(offer,offer_dict[offer])

        print "offers cart:"
        print self.offers_cart


    @api.one
    def _verify_cart_offers(self,offer,order_lines):
        if(offer.date_end > fields.Datetime.now()):
            if(offer.offer_type == 1):
                #bundle
                pass
                
            elif(offer.offer_type == 2):
               #nxm
               print "n x m"
               self._apply_n_x_m(offer,order_lines)

            elif (offer.offer_type == 3):
                #nxprezzo
                #if len(selected_prod) >= offer.n
                pass
       
    @api.one
    def _apply_n_x_m(self,offer,order_lines):
        #in caso serva di cancellare tutte le order line
        for pl2 in self.env['netaddiction.order.specialoffer.cart.history'].search([("create_uid","=",1)]):
            pl2.unlink()
        print "calling apply nxm for offer %s" %offer.name
        tot_qty = 0
        for ol in order_lines:
            tot_qty += ol.product_uom_qty

        if tot_qty >= offer.n and offer.n > 0:
            print "A)"
            part = tot_qty//offer.n
            num_prod_for_free = part * (offer.n - offer.m)
            i = 0
            #order lines non prodotti
            order_lines.sort(key=lambda ol: ol.price_unit)
            print len (order_lines)
            print order_lines
            while i < num_prod_for_free:
                print "B)"
                ol = order_lines[i] if order_lines[i] else None
                print "prodotto %s quantità %s" % (ol.product_id,ol.product_uom_qty)
                if(ol and ol.product_uom_qty <= num_prod_for_free - i):
                    print "C)"
                    offer_line = ol.product_id.offer_cart_lines[0]
                    ptint "qty_max_buyable %s" %offer_line.qty_max_buyable
                    if (offer_line.qty_max_buyable > 0 and ol.product_uom_qty > offer_line.qty_max_buyable):
                            raise QtyMaxBuyableException(ol.product_id.name)
                    else:
                        ol.price_unit = 0.0
                        i += int(ol.product_uom_qty)
                        self.env['netaddiction.order.specialoffer.cart.history'].create({'product_id' : ol.product_id.id, 'order_id' : self.id, 'offer_type':offer_line.offer_type, 'qty' : ol.product_uom_qty,'n' :offer_line.offer_cart_id.n,'m' :offer_line.offer_cart_id.m,'bundle_price': offer_line.offer_cart_id.bundle_price, 'offer_author_id' :offer_line.offer_cart_id.author_id.id, 'offer_name' : offer_line.offer_cart_id.name })
                        
                elif ol:
                    if (offer_line.qty_max_buyable > 0 and ol.product_uom_qty > offer_line.qty_max_buyable):
                            raise QtyMaxBuyableException(ol.product_id.name)
                    offer_line = ol.product_id.offer_cart_lines[0]
                    print "split line"
                    self._split_order_line(ol,num_prod_for_free -i,ol.product_uom_qty - (num_prod_for_free -i))
                    ol.price_unit = 0.0
                    self.env['netaddiction.order.specialoffer.cart.history'].create({'product_id' : ol.product_id.id, 'order_id' : self.id, 'offer_type':offer_line.offer_type, 'qty' : ol.product_uom_qty,'n' :offer_line.offer_cart_id.n,'m' :offer_line.offer_cart_id.m,'bundle_price': offer_line.offer_cart_id.bundle_price, 'offer_author_id' :offer_line.offer_cart_id.author_id.id, 'offer_name' : offer_line.offer_cart_id.name })
                    #spezza le linee

                    i = num_prod_for_free
#sposta sopra solo per le linee incluse nell'offerta
            # for ol in order_lines:
            #     offer_line = ol.product_id.offer_cart_lines[0]
            #     self.env['sale.order.line'].create({'product_id' : ol.product_id, 'order_id' : self.id, 'offer_type':offer_line.offer_type, 'qty' : ol.product_uom_qty,'n' :offer_line.n,'m' :offer_line.m,'bundle_price': offer_line.bundle_price, 'offer_author_id' :offer_line.offer_author_id, 'offer_name' : offer_line.offer_name })
            #     print "add offer line"
            #     if(offer_line.qty_limit > 0 and offer_line.qty_selled + ol.product_uom_qty > offer_line.qty_limit):
            #         #TODO: aggiungi notifica (e manda mail a riccardo in action problems)
            #         #molto importante perchè così quando viene chiamato action_confirm l'ordine viene spostato in problem
            #         pass

    @api.one
    def _split_order_line(self,order_line,qty_1,qty_2):
        """splitta una order line in due diverse order line (sempre dentro lo stesso ordine) rispettivamente di quantità qty_1 e qty_2
            per fare ciò assegna qty_1 alla quantità di order_linee ne crea una nuova con quantità qty_2
            ritorna None se qty_1 + qty_2 != order_line.product_uom_qty, altimenti un riferimento alla nuova order_line
        """
        if qty_1 + qty_2 != order_line.product_uom_qty:
            return None
        else:
            print "x"
            order_line.product_uom_qty = qty_1
            print "y"
            order_line.product_uom_change()
            
            print "z"
            print qty_1
            print qty_2
            ret = self.env['sale.order.line'].create({'product_id':order_line.product_id.id, 'order_id' : self.id, 'product_uom' : order_line.product_uom.id,'product_uom_qty' : qty_2 , 'name' : order_line.name,})
            ret.product_id_change()
            return ret


class OrderOfferCartHistory(models.Model):

    _name = "netaddiction.order.specialoffer.cart.history"
    
    

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_type = fields.Selection([(1,'Bundle'),(2,'n x m'),(3,'n x prezzo')], string='Tipo Offerta', default=2,required=True)
    qty = fields.Integer(string = "quantità")
    n = fields.Integer(string="N")
    m = fields.Integer(string="M")
    bundle_price = fields.Integer(string="Prezzo bundle")
    n_price = fields.Integer(string= "Prezzo Prodotti")
    offer_author_id = fields.Many2one(comodel_name='res.users',string='Autore offerta')
    offer_name = fields.Char(string='Offerta')
    order_id = fields.Many2one(comodel_name='sale.order', string='Ordine',index=True, copy=False, required=True)




        
