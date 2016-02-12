# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class CatalogOffer(models.Model):

    _name = "netaddiction.specialoffer.catalog"


    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=True)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    author_id = fields.Many2one(comodel_name='res.users',string='Autore', required=True)
    date_start = fields.Datetime('Start Date', help="Data di inizio della offerta", required=True)
    date_end = fields.Datetime('End Date', help="Data di fine dell'offerta", required=True)
    priority = fields.Selection([(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], string='Priorità', default=1,required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato" )
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato")
    qty_min = fields.Integer( string='Quantità minima acquisto', help = "Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.")
    qty_selled = fields.Integer( string='Quantità venduta', default=0)
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta', default=2)
    fixed_price = fields.Integer(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    products_list = fields.One2many('netaddiction.specialoffer.offer_catalog_line', 'offer_catalog_id', string='Lista prodotti')
    # filter_type = fields.Selection([(1,'Espressione'),(2,"lista prodotti")], required=True)

    #BUG noto: se nella vista scrivi -1 su fixed price  poi cambi a percent discount riesci a scrivere il -1
    #TODO:Non funziona bene nella vista, da sistemare
    
    @api.one
    @api.constrains('fixed_price','offer_type')
    def _check_fixed_price(self):
        if  self.offer_type == 1 and self.fixed_price <= 0:
            raise ValidationError("Il valore del prezzo fisso non può essere minore  o uguale di zero")

    @api.one
    @api.constrains('percent_discount','offer_type')
    def _check_percent_discount(self):
        if self.offer_type == 2 and (self.percent_discount <= 0 or self.percent_discount > 100):
            raise ValidationError("Il valore dello sconto percentuale non può essere minore di 0 o maggiore di 100")

    # @api.one
    # @api.constrains('products_list')
    # def _check_product_list(self):
    #     if len(self.products_list) <1:
    #          raise ValidationError("Inserisci almeno un prodotto nella lista")



    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):

        if(self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")


    @api.one
    @api.constrains('priority')
    def _check_priority(self):
        for pl in self.products_list:
            pl.priority = self.priority

    @api.model
    def create(self,values):
        
        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        """
        now = fields.Date.today()
        if (values['date_start'] and values['date_start'] < now): 
            raise ValidationError("Data inizio offerta non può essere prima della data odierna")
        elif (values['date_end'] and values['date_end'] < now): 
            raise ValidationError("Data fine offerta non può essere prima della data odierna")

        return  super(CatalogOffer, self).create(values)


    @api.multi
    def populate_products_from_expression(self):
        if self.expression_id:
            dom = self.expression_id.find_products_domain()
            ids = []
            to_add =[]
            for pl in self.products_list:
                ids.append(pl.product_id.id)
            print ids
            for prod in self.env['product.product'].search(dom):
                if( prod.id not in ids):
                    to_add.append(self.env['netaddiction.specialoffer.offer_catalog_line'].create({'product_id':prod.id, 'offer_catalog_id' : self.id, 'qty_max_buyable' : self.qty_max_buyable,'qty_limit': self.qty_limit, 'qty_min':self.qty_min,'offer_type':self.offer_type,'percent_discount':self.percent_discount,'fixed_price': self.fixed_price, 'priority' : self.priority}))
            products_list = [(0,0, to_add)]


    @api.multi
    def remove_products(self):
        # for pl2 in self.env['netaddiction.specialoffer.offer_catalog_line'].search([("create_uid","=",1)]):
        #     pl2.unlink()
        for pl in self.products_list:
            pl.unlink()

    @api.multi
    def modify_products(self):
        for pl in self.products_list:
            pl.qty_max_buyable = self.qty_max_buyable
            pl.qty_limit = self.qty_limit
            pl.qty_min = self.qty_min
            pl.offer_type = self.offer_type
            pl.percent_discount = self.percent_discount
            pl.fixed_price = self.fixed_price
            pl.priority = self.priority




class ShoppingCartOffer(models.Model):

    _name = "netaddiction.specialoffer.cart"


    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla",default=True)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    author_id = fields.Many2one(comodel_name='res.users',string='Autore', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    date_start = fields.Datetime('Start Date', help="Data di inizio della offerta", required=True)
    date_end = fields.Datetime('End Date', help="Data di fine dell'offerta", required=True)
    list_prod = fields.One2many(comodel_name='product.product',compute='populate_products')
    priority = fields.Selection([(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], string='Priorità', default=1,required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_min = fields.Integer( string='Quantità minima acquisto', help = "Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.", required=True)
    qty_selled = fields.Integer( string='Quantità venduta', default=0)
    offer_type = fields.Selection([(1,'Bundle'),(2,'n x m'),(3,'n x prezzo')], string='Tipo Offerta', default=2,required=True)
    n = fields.Integer(string="N")
    m = fields.Integer(string="M")
    bundle_price = fields.Integer(string="Prezzo bundle")
    n_price = fields.Integer(string= "Prezzo Prodotti")

   # products_list = fields.One2many('netaddiction.specialoffer.product_line', 'offer_cart_id', string='Lista prodotti')
    filter_type = fields.Selection([(1,'Espressione'),(2,"lista prodotti")], required=True)


    


    @api.one
    @api.constrains('n','m','offer_type')
    def _check_n_m(self):
        if(self.offer_type == 2):
            if(self.n <= 0 or self.m <= 0):
                raise ValidationError("n e m devono essere  > 0")
            if(self.n <= self.m):
                raise ValidationError("n deve essere maggiore di m! (es. 3x2)")

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
       if(self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")

    @api.one
    @api.constrains('filter_type', 'products_list')
    def _check_product_list(self):
        if self.filter_type == 2 and len(self.products_list) <1:
             raise ValidationError("Inserisci almeno un prodotto nella lista")

    @api.one
    @api.constrains('offer_type', 'n','n_price')
    def _check_n_x_price(self):
        if self.offer_type == 3:
            if(self.n <= 0):
                raise ValidationError("n deve essere  > 0")
            if(self.n_price <= 0):
                raise ValidationError("il prezzo fisso deve essere  > 0")

    @api.one
    @api.constrains('filter_type', 'expression_id')
    def _check_expression(self):

        if self.filter_type == 1 and  len(self.expression_id) < 1:
             raise ValidationError("Scegli una Espressione")

    @api.model
    def create(self,values):
        
        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        """
        now = fields.Date.today()
        if (values['date_start'] and values['date_start'] < now): 
            raise ValidationError("Data inizio offerta non può essere prima della data odierna")
        elif (values['date_end'] and values['date_end'] < now): 
            raise ValidationError("Data fine offerta non può essere prima della data odierna")

        return  super(ShoppingCartOffer, self).create(values)

    @api.multi
    def find_products(self):
        return self.expression_id.find_products()

    @api.multi
    def populate_products(self):
        dom = self.expression_id.find_products_domain()
        ids =[]
        for prod in self.env['product.product'].search(dom):
            ids.append(prod.id)
        self.list_prod = [(6,0,ids)]



class OfferCatalogLine(models.Model):

    _name = "netaddiction.specialoffer.offer_catalog_line"
    _order = "priority"
    


    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_catalog_id = fields.Many2one('netaddiction.specialoffer.catalog', string='Offerta catalogo', index=True, copy=False, required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_min = fields.Integer( string='Quantità minima acquisto', help = "Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.", required=True)
    fixed_price = fields.Integer(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta')
    qty_selled = fields.Integer( string='Quantità venduta', default=0)
    priority = fields.Integer(string="priorità", default = 0)

    @api.one
    @api.constrains('fixed_price','offer_type')
    def _check_fixed_price(self):
        if self.offer_type == 1 and self.fixed_price <= 0:
            raise ValidationError("Il valore del prezzo fisso non può essere minore  o uguale di zero")

    @api.one
    @api.constrains('percent_discount','offer_type')
    def _check_percent_discount(self):
        if self.offer_type == 2 and (self.percent_discount <= 0 or self.percent_discount > 100):
            raise ValidationError("Il valore dello sconto percentuale non può essere minore di 0 o maggiore di 100")


    @api.one
    @api.constrains('offer_catalog_id')
    def _check_priority(self):
        self.priority = self.offer_catalog_id[0].priority


       
   
           

        


