# -*- coding: utf-8 -*-
from openerp import models, fields, api
from offers_product import QtyMaxBuyableException
from collections import Counter

class OfferOrder(models.Model):
    _inherit = 'sale.order'

    offers_cart = fields.One2many('netaddiction.order.specialoffer.cart.history','order_id', string='offerte carrello attive')

    
    def _check_offers_catalog(self):
        """controlla le offerte catalogo e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit per la sua offerta catalogo corrispondente
        False altrimenti
        """
        problems = False
        if( self.state == 'draft'):
            for line in self.order_line:
                if( line.offer_type and  not line.negate_offer ):
                    offer_line = line.product_id.offer_catalog_lines[0] if len(line.product_id.offer_catalog_lines) >0 else None
                    if offer_line:
                        offer_line.qty_selled += line.product_uom_qty
                        offer_line.active = offer_line.qty_limit == 0 or offer_line.qty_selled <= offer_line.qty_limit
                    if(offer_line.qty_limit >0 and offer_line.qty_selled > offer_line.qty_limit):
                        problems = True

        return problems

    
    def _check_offers_cart(self):
        """controlla le offerte carrello e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit per la sua offerta carrello corrispondente
        False altrimenti
        """

        problems = False
        if( self.state == 'draft'):
            for och in self.offers_cart:

                    offer_line = och.offer_cart_line
                    if offer_line:
                        offer_line.qty_selled += och.qty
                        offer_line.active = offer_line.qty_limit == 0 or offer_line.qty_selled <= offer_line.qty_limit
                    if(offer_line.qty_limit >0 and offer_line.qty_selled > offer_line.qty_limit):
                        problems = True

        return problems

    @api.one
    def action_problems(self):
        self._check_offers_catalog()
        self._check_offers_cart()
    	self.state = 'problem'


    @api.multi
    def action_confirm(self):
        problems = False
    	for order in self:
            problems = order._check_offers_catalog() 
            problems = order._check_offers_cart() or problems
            #TODO se c'è un commento spostare in problem non in sale
            if problems:
            #TODO aggiungere il commento sul perchè
                order.state = 'problem'
            else:
                super(OfferOrder, order).action_confirm()
    
    @api.multi
    def action_cancel(self):
        #N.B. offerte mai riattivate manualmente
        self._send_cancel_mail()
        for order in self:
            if (order.state != 'draft'):
                #offerte catalogo
                for line in order.order_line:
                    if( line.offer_type  and not line.negate_offer):
                        offer_line = order.product_id.offer_catalog_lines[0] if len(order.product_id.offer_catalog_lines) >0 else None
                        if offer_line:
                            offer_line.qty_selled -= line.product_uom_qty
                #offerte carrello
                for och in order.offers_cart:
                    offer_line = och.offer_cart_line
                    if offer_line:
                        offer_line.qty_selled -= och.qty

        super(OfferOrder, self).action_cancel()



    #comportamento su offerte spente: vanno riattivate sempre manualmente
    @api.one
    def extract_cart_offers(self):
        """Metodo per controllare se ci sono offerte carrello attive sui prodotti nell'ordine.
            Ritorna la lista delle offerte ordinata per priorità
            Raise QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable
        """
        #cancello tutte le history line di questo ordine
        for och in self.env['netaddiction.order.specialoffer.cart.history'].search([("order_id","=",self.id)]):
            #TODO CONTROLLARE CHE I PREZZI TORNINO DI DEFAULT!
            och.unlink()
        # #chiavi = offerte carrello che hanno una possibilità di essere applicate a questo ordine
        # #valori = lista di (order_line)
        # offer_dict = {} 
        # #lista ordinata per priorità di offerte carrello che hanno una possibilità di essere applicate a questo ordine
        # offer_list = []
        # for ol in self.order_line:
           
        #     if len(ol.product_id.offer_cart_lines) > 0:
        #         offer = ol.product_id.offer_cart_lines[0].offer_cart_id
        #         if offer not in offer_dict:
        #             prod_list =[]
        #             prod_list.append(ol)
        #             offer_dict[offer] = prod_list
        #         else:
        #             offer_dict[offer].append(ol)


        # offer_list = offer_dict.keys()
        # offer_list.sort(key=lambda offer: offer.priority)
        # order_lines = [o for o in self.order_line]
        
        # #controllo scadenze offerta
        # for offer in offer_list:
        #     self._verify_cart_offers(offer,offer_dict[offer])


        # new version

        offer_list = []
        #offer ->[lista product id]
        offer_dict = {}
        #order lines utilizzabili
        order_lines_usables = []
        for ol in self.order_line:
            if len(ol.product_id.offer_cart_lines) > 0:
                #considero solo order lines che hanno almeno una offerta carrello ME GUSTA
                order_lines_usables.append(ol.id) 
                for offer in ol.product_id.offer_cart_lines:
                    if offer.offer_cart_id not in offer_dict:
                        prod_list =[]
                        prod_list.append(ol.product_id.id)
                        offer_dict[offer.offer_cart_id] = prod_list
                    else:
                        offer_dict[offer.offer_cart_id].append(ol.product_id.id)

        offer_list = offer_dict.keys()
        offer_list.sort(key=lambda offer: offer.priority)

        for offer in offer_list:
            if not order_lines_usables:
                break
            self._verify_cart_offers(offer,offer_dict[offer],order_lines_usables)




    @api.one
    def _verify_cart_offers(self,offer,pid_list,order_lines_usables):
        """Verifica se l'offerta offer è verificata per le linee order_lines e in caso la applica
        """
        #controllo scadenze offerta
        if(offer.date_end > fields.Datetime.now()):
            if(offer.offer_type == 1):
                #bundle
                print "bundle"
                self._apply_bundle(offer,pid_list,order_lines_usables)
                
                
                
            elif(offer.offer_type == 2):
               #nxm
               print "n x m"
               self._apply_n_x_m(offer,pid_list,order_lines_usables)

            elif (offer.offer_type == 3):
                #nxprezzo
                print "n x price"
                self._apply_n_x_price(offer,pid_list,order_lines_usables)
                
       
    @api.one
    def _apply_n_x_m(self,offer,pid_list,order_lines_usables):
        """ applica l'offerta n x m offer alle order_lines in questo ordine
        """
        order_lines =[]
        for ol in self.order_line:
            if ol.id in order_lines_usables and ol.product_id.id in pid_list:
                order_lines.append(ol)
        tot_qty = 0
        for ol in order_lines:
            tot_qty += ol.product_uom_qty

        if tot_qty >= offer.n and offer.n > 0:
            #divisione intera
            part = tot_qty//offer.n
            num_prod_for_free = part * (offer.n - offer.m)
            #ordino le order lines per price unit crescente
            order_lines.sort(key=lambda ol: ol.price_unit)
            self._create_offer_cart_history_n(offer.n * part, order_lines,offer)
            i = 0
            for ol in order_lines:
               
                if(ol.product_uom_qty <= num_prod_for_free - i):
                    ol.price_unit = 0.0
                    order_lines_usables.remove(ol.id)
                    i += int(ol.product_uom_qty)
                        
                elif ol:
                    #spezza le linee
                    res = self._split_order_line(ol,num_prod_for_free -i,ol.product_uom_qty - (num_prod_for_free -i))
                    order_lines_usables.remove(ol.id)
                    ol.price_unit = 0.0
                    new_ol = res[0] if res[0] else None
                    if new_ol:
                        order_lines_usables.append(new_ol.id)
                    i = num_prod_for_free
                #EXIT CONDITION
                if i >= num_prod_for_free:
                    break

    @api.one
    def _apply_n_x_price(self,offer,pid_list,order_lines_usables):
        """ applica l'offerta n x prezzo offer alle order_lines in questo ordine
        """
        order_lines =[]
        for ol in self.order_line:
            if ol.id in order_lines_usables and ol.product_id.id in pid_list:
                order_lines.append(ol)
        tot_qty = 0
        for ol in order_lines:
            tot_qty += ol.product_uom_qty
        if tot_qty >= offer.n and offer.n > 0:
            #divisione intera
            part = tot_qty//offer.n
            num_prod_to_reduce = part * offer.n
            #ordino le order lines per price unit crescente
            order_lines.sort(key=lambda ol: ol.price_unit)
            self._create_offer_cart_history_n(offer.n * part, order_lines,offer)
            i = 0
            for ol in order_lines:
            
                if(ol and ol.product_uom_qty <= num_prod_to_reduce - i):
                    tax = ol.tax_id.amount
                    detax = offer.n_price / (float(1) + float(tax/100))
                    deiva = round(detax,2)
                    ol.price_unit = deiva
                    order_lines_usables.remove(ol.id)
                    i += int(ol.product_uom_qty)
                        
                elif ol:
                    #spezza le linee
                    res = self._split_order_line(ol,num_prod_to_reduce -i,ol.product_uom_qty - (num_prod_to_reduce -i))
                    tax = ol.tax_id.amount
                    detax = offer.n_price / (float(1) + float(tax/100))
                    deiva = round(detax,2)
                    ol.price_unit = deiva
                    order_lines_usables.remove(ol.id)
                    new_ol = res[0] if res[0] else None
                    if new_ol:
                        order_lines_usables.append(new_ol.id)
                    i = num_prod_to_reduce

                #EXIT CONDITION
                if i >= num_prod_to_reduce:
                    break

    @api.one
    def _apply_bundle(self,offer,pid_list,order_lines_usables):
        """ applica l'offerta bundle offer alle order_lines in questo ordine
        """

        order_lines =[]
        for ol in self.order_line:
            if ol.id in order_lines_usables and ol.product_id.id in pid_list:
                order_lines.append(ol)

        bundle_prods =[ocl.product_id.id for ocl in offer.products_list]
        order_prods = []
        for ol in order_lines:
            i = 0
            while i < ol.product_uom_qty:
                order_prods.append(ol.product_id.id)
                i += 1

        if len(order_prods) >= len(bundle_prods):

            order_cnt = Counter(order_prods)
            bundle_cnt = Counter(bundle_prods)
            bundle_verified = True
            for bundle_pid in bundle_prods:
                if bundle_cnt[bundle_pid] > order_cnt[bundle_pid]:
                    bundle_verified = False
                    break
            if bundle_verified:
                #history e cambio prezzi
                #matches = [ol for ol in order_lines if ol.product_id.id in bundle_prods]
                self._create_offer_cart_history_bundles(bundle_cnt,order_lines,offer)
                tot = 0
                for ol in order_lines:
                    if ol.product_uom_qty >bundle_cnt[ol.product_id.id]:
                        #split line
                        res = self._split_order_line(ol,bundle_cnt[ol.product_id.id],ol.product_uom_qty - bundle_cnt[ol.product_id.id])
                        new_ol = res[0] if res[0] else None
                        if new_ol:
                            order_lines_usables.append(new_ol.id)

                    order_lines_usables.remove(ol.id)
                    tot += ol.price_total
                bundle_price = offer.bundle_price
                for ol in order_lines:
                    #qui siamo sicuri che product_uom_qty = bundle_cnt[ol.product_id.id]
                    res = self._find_bundle_unit_price(ol,tot,bundle_price)
                    print type(res)
                    print res
                    ol.price_unit = res
                        
                







        


    @api.one
    def _split_order_line(self,order_line,qty_1,qty_2):
        """Splitta una order line in due diverse order line (sempre dentro lo stesso ordine) rispettivamente di quantità qty_1 e qty_2
            per fare ciò assegna qty_1 alla quantità di order_linee ne crea una nuova con quantità qty_2
            ritorna None se qty_1 + qty_2 != order_line.product_uom_qty, altimenti un riferimento alla nuova order_line
        """
        if qty_1 + qty_2 != order_line.product_uom_qty:
            return None
        else:
            order_line.product_uom_qty = qty_1
            order_line.product_uom_change()
            ret = self.env['sale.order.line'].create({'product_id':order_line.product_id.id, 'order_id' : self.id, 'product_uom' : order_line.product_uom.id,'product_uom_qty' : qty_2 , 'name' : order_line.name,})
            ret.product_id_change()
            return ret

    @api.one
    def _create_offer_cart_history_n(self,num, order_lines,offer):
        """ Questo metodo crea le OrderOfferCartHistory per l'offerta nxm o nxprice che accomuna tutte le order_lines. Le order_lines vengono visitate dall'inizio fino al raggiungimento di num (quindi le order_lines devono essere già ordinate secondo un criterio sensato)
            num = numero di prodotti a cui deve essere applicata l'offerta (anche quelli che non saranno scontati nel caso del n x m)
            Raise QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable
        """
        i = 0

        for ol in order_lines:
            

            to_add = int(ol.product_uom_qty) if (i + ol.product_uom_qty < num) else (num - i)
            offer_line = None
            for ofcl in ol.product_id.offer_cart_lines:
                if ofcl.offer_cart_id.id == offer.id:
                    offer_line = ofcl
                    break
            if offer_line:
                
                if offer_line.qty_max_buyable > 0 and to_add > offer_line.qty_max_buyable:
                #pulizia dei record history già creati
                    offers_cart_history = self.env['netaddiction.order.specialoffer.cart.history'].search([("order_id","=",self.id),("offer_name","=",offer_line.offer_cart_id.name)])
                    for och in offers_cart_history:
                        och.unlink()
                    raise QtyMaxBuyableException(ol.product_id.name,ol.product_id.id)
                else:
                    
                    self.env['netaddiction.order.specialoffer.cart.history'].create({'product_id' : ol.product_id.id, 'order_id' : self.id, 'offer_type':offer_line.offer_type, 'qty' : to_add,'n' :offer_line.offer_cart_id.n,'m' :offer_line.offer_cart_id.m,'bundle_price': offer_line.offer_cart_id.bundle_price, 'offer_author_id' :offer_line.offer_cart_id.author_id.id, 'offer_name' : offer_line.offer_cart_id.name,  'offer_cart_line' : offer_line.id , 'n_price' : offer.n_price})
                    i +=  to_add
            #EXIT CONDITION
            if i >= num:
                break


    @api.one
    def _create_offer_cart_history_bundles(self,bundle_cnt, order_lines,offer):
        """ Questo metodo crea le OrderOfferCartHistory per l'offerta BUNDLE che accomuna tutte le order_lines. Le order_lines vengono visitate tutte
            bundle_cnt = Counter per i prodotti nel bundle
            Raise QtyMaxBuyableException nel caso in cui sia stata superata una qty_max_buyable
        """
        for ol in order_lines:
            offer_line = None
            for ofcl in ol.product_id.offer_cart_lines:
                if ofcl.offer_cart_id.id == offer.id:
                    offer_line = ofcl
                    break
            if (offer_line.qty_max_buyable > 0 and bundle_cnt[ol.product_id.id] > offer_line.qty_max_buyable):
                #pulizia dei record history già creati
                offers_cart_history = self.env['netaddiction.order.specialoffer.cart.history'].search([("order_id","=",self.id),("offer_name","=",offer_line.offer_cart_id.name)])
                for och in offers_cart_history:
                    och.unlink()
                raise QtyMaxBuyableException(ol.product_id.name,ol.product_id.id)
            else:
                self.env['netaddiction.order.specialoffer.cart.history'].create({'product_id' : ol.product_id.id, 'order_id' : self.id, 'offer_type':offer_line.offer_type, 'qty' : bundle_cnt[ol.product_id.id],'n' :offer_line.offer_cart_id.n,'m' :offer_line.offer_cart_id.m,'bundle_price': offer_line.offer_cart_id.bundle_price, 'offer_author_id' :offer_line.offer_cart_id.author_id.id, 'offer_name' : offer_line.offer_cart_id.name, 'offer_cart_line' : offer_line.id })

    
    def _find_bundle_unit_price(self,ol,tot,bundle_price):
        """tot = totale con iva della somma dei prodotti bundle nell'ordine
        bundle_price = prezzo del bundle (che deve essere ottenuto  nell'ordine)
        returns il prezzo pesato de-ivato del prodotto nella ol.

        """
        full_price =((ol.price_total/ol.product_uom_qty) * bundle_price) / tot
        tax = ol.tax_id.amount
        detax = full_price / (float(1) + float(tax/100))
        deiva = round(detax,2)
        return float(deiva)



class OrderOfferCartHistory(models.Model):

    _name = "netaddiction.order.specialoffer.cart.history"
    
    

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_type = fields.Selection([(1,'Bundle'),(2,'n x m'),(3,'n x prezzo')], string='Tipo Offerta', default=2,required=True)
    qty = fields.Integer(string = "quantità")
    n = fields.Integer(string="N")
    m = fields.Integer(string="M")
    bundle_price = fields.Float(string="Prezzo bundle")
    n_price = fields.Float(string= "Prezzo Prodotti")
    offer_author_id = fields.Many2one(comodel_name='res.users',string='Autore offerta')
    offer_name = fields.Char(string='Offerta')
    order_id = fields.Many2one(comodel_name='sale.order', string='Ordine',index=True, copy=False, required=True)
    offer_cart_line = fields.Many2one(comodel_name='netaddiction.specialoffer.offer_cart_line')





        
