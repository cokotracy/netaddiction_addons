# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID


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
    qty_selled = fields.Float( string='Quantità venduta', default=0.0, compute="_compute_qty_selled")
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta', default=2)
    fixed_price = fields.Float(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    products_list = fields.One2many('netaddiction.specialoffer.offer_catalog_line', 'offer_catalog_id', string='Lista prodotti')
    end_cron_job = fields.Integer()
    start_cron_job = fields.Integer()


    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active:
            for pl in self.products_list:
                pl.active = False
            

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):

        if(self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")
        for cron in self.env['ir.cron'].search([('id','=',self.end_cron_job)]):
            cron.nextcall = self.date_end


    @api.one
    @api.constrains('priority')
    def _check_priority(self):
        for pl in self.products_list:
            pl.priority = self.priority

    @api.model
    def create(self,values):
        
        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        e creo i cron
        """
        now = fields.Date.today()
        if (values['date_start'] and values['date_start'] < now): 
            raise ValidationError("Data inizio offerta non può essere prima della data odierna")
        elif (values['date_end'] and values['date_end'] < now): 
            raise ValidationError("Data fine offerta non può essere prima della data odierna")

        res = super(CatalogOffer, self).create(values)


        timesheet_id = 1
        nextcall = res.date_end
        name = "[Scadenza]Cron job per offerta id %s" %res.id
        res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr,self.env.uid,{
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.catalog',
                'function': 'turn_off',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall' : "1",

            })
        if res.date_start > fields.Datetime.now():
            res.active = False
            for pl in res.products_list:
                pl.active = False
            timesheet_id = 1
            nextcall = res.date_start
            name = "[Inizio]Cron job per offerta id %s" %res.id
            res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr,self.env.uid,{
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.catalog',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall' : "1",

            })            
        
        return res


    @api.one
    def populate_products_from_expression(self):
        if self.expression_id:
            dom = self.expression_id.find_products_domain()
            ids = []
            to_add =[]
            for pl in self.products_list:
                ids.append(pl.product_id.id)

            for prod in self.env['product.product'].search(dom):
                if( prod.id not in ids):
                    to_add.append(self.env['netaddiction.specialoffer.offer_catalog_line'].create({'product_id':prod.id, 'offer_catalog_id' : self.id, 'qty_max_buyable' : self.qty_max_buyable,'qty_limit': self.qty_limit, 'qty_min':self.qty_min,'offer_type':self.offer_type,'percent_discount':self.percent_discount,'fixed_price': self.fixed_price, 'priority' : self.priority}))
            


    @api.multi
    def remove_products(self):
        #in caso serva di cancellare tutte le order line
        # for pl2 in self.env['netaddiction.specialoffer.offer_catalog_line'].search([("create_uid","=",1)]):
        #     pl2.unlink()
            
        for offer in self:
            for pl in offer.products_list:
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

    @api.one
    def turn_off(self):
        for pl in self.products_list:
            pl.active = False
           
        self.write({'active' : False})

    @api.one
    def turn_on(self):
        for pl in self.env['netaddiction.specialoffer.offer_catalog_line'].search([('offer_catalog_id','=',self.id),('active','=',False)]):
            pl.active = True
           
        self.write({'active' : True})

        


    @api.multi
    def _compute_qty_selled(self):
        for offer in self:
            temp = 0.0
            for pl in offer.products_list:
                 temp += pl.qty_selled
            for pl in self.env['netaddiction.specialoffer.offer_catalog_line'].search([('offer_catalog_id','=',offer.id),('active','=',False)]):
                temp += pl.qty_selled
            #search for inactive offers
            offer.qty_selled = temp


class OfferCatalogLine(models.Model):

    _name = "netaddiction.specialoffer.offer_catalog_line"
    _order = "priority"
    

    active = fields.Boolean(default=True,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_catalog_id = fields.Many2one('netaddiction.specialoffer.catalog', string='Offerta catalogo', index=True, copy=False, required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_min = fields.Integer( string='Quantità minima acquisto', help = "Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.", required=True)
    fixed_price = fields.Float(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta')
    qty_selled = fields.Float( string='Quantità venduta', default=0.0)
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
        self.offer_type = self.offer_catalog_id[0].offer_type

    


class ShoppingCartOffer(models.Model):

    _name = "netaddiction.specialoffer.cart"


    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla",default=True)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    author_id = fields.Many2one(comodel_name='res.users',string='Autore', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    date_start = fields.Datetime('Start Date', help="Data di inizio della offerta", required=True)
    date_end = fields.Datetime('End Date', help="Data di fine dell'offerta", required=True)
    
    priority = fields.Selection([(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], string='Priorità', default=1,required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_selled = fields.Integer( string='Quantità venduta', default=0.0, compute="_compute_qty_selled")
    offer_type = fields.Selection([(1,'Bundle'),(2,'n x m'),(3,'n x prezzo')], string='Tipo Offerta', default=2,required=True)
    n = fields.Integer(string="N")
    m = fields.Integer(string="M")
    bundle_price = fields.Float(string="Prezzo bundle")
    n_price = fields.Float(string= "Prezzo Prodotti")
    products_list = fields.One2many('netaddiction.specialoffer.offer_cart_line', 'offer_cart_id', string='Lista prodotti')
    end_cron_job = fields.Integer()
    start_cron_job = fields.Integer()


    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active:
            for pl in self.products_list:
                pl.active = False

    @api.one
    @api.constrains('priority')
    def _check_priority(self):
        for pl in self.products_list:
            pl.priority = self.priority


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
        for cron in self.env['ir.cron'].search([('id','=',self.end_cron_job)]):
            cron.nextcall = self.date_end




    @api.one
    @api.constrains('offer_type', 'n','n_price')
    def _check_n_x_price(self):
        if self.offer_type == 3:
            if(self.n <= 0):
                raise ValidationError("n deve essere  > 0")
            if(self.n_price <= 0):
                raise ValidationError("il prezzo fisso deve essere  > 0")



    @api.one
    def turn_off(self):
        for pl in self.products_list:
            pl.active = False
           
        self.write({'active' : False})

    @api.one
    def turn_on(self):
        for pl in self.env['netaddiction.specialoffer.offer_cart_line'].search([('offer_cart_id','=',self.id),('active','=',False)]):
            pl.active = True
           
        self.write({'active' : True})





    @api.model
    def create(self,values):
        
        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        e creo i cron
        """
        now = fields.Date.today()
        if (values['date_start'] and values['date_start'] < now): 
            raise ValidationError("Data inizio offerta non può essere prima della data odierna")
        elif (values['date_end'] and values['date_end'] < now): 
            raise ValidationError("Data fine offerta non può essere prima della data odierna")

        res = super(ShoppingCartOffer, self).create(values)


        timesheet_id = 1
        nextcall = res.date_end
        name = "[Scadenza]Cron job per offerta id %s" %res.id
        res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr,self.env.uid,{
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.cart',
                'function': 'turn_off',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall' : "1",

            })
        if res.date_start > fields.Datetime.now():


            res.active = False
            for pl in res.products_list:
                pl.active = False
            timesheet_id = 1
            nextcall = res.date_start
            name = "[Inizio]Cron job per offerta id %s" %res.id
            res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr,self.env.uid,{
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.cart',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall' : "1",

            })            
        
        return res

    @api.one
    def populate_products_from_expression(self):
        if self.expression_id:
            dom = self.expression_id.find_products_domain()
            ids = []
            to_add =[]
            for pl in self.products_list:
                ids.append(pl.product_id.id)

            for prod in self.env['product.product'].search(dom):
                if( prod.id not in ids):
                    to_add.append(self.env['netaddiction.specialoffer.offer_cart_line'].create({'product_id':prod.id, 'offer_cart_id' : self.id, 'qty_max_buyable' : self.qty_max_buyable,'qty_limit': self.qty_limit, 'offer_type':self.offer_type, 'priority' : self.priority}))
        


    @api.multi
    def remove_products(self):
        #in caso serva di cancellare tutte le order line
        # for pl2 in self.env['netaddiction.specialoffer.offer_catalog_line'].search([("create_uid","=",1)]):
        #     pl2.unlink()    
        for offer in self:
            for pl in offer.products_list:
                pl.unlink()
        

    @api.multi
    def modify_products(self):
        for pl in self.products_list:
            pl.qty_max_buyable = self.qty_max_buyable
            pl.qty_limit = self.qty_limit
            pl.offer_type = self.offer_type
            pl.priority = self.priority

    @api.multi
    def _compute_qty_selled(self):
        for offer in self:
            temp = 0.0
            for pl in offer.products_list:
                 temp += pl.qty_selled
            for pl in self.env['netaddiction.specialoffer.offer_cart_line'].search([('offer_cart_id','=',offer.id),('active','=',False)]):
                temp += pl.qty_selled
            #search for inactive offers
            offer.qty_selled = temp


       
class OfferCartLine(models.Model):

    _name = "netaddiction.specialoffer.offer_cart_line"
    _order = "priority"
    

    active = fields.Boolean(default=True,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_cart_id = fields.Many2one('netaddiction.specialoffer.cart', string='Offerta Carrello', index=True, copy=False, required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    offer_type = fields.Selection([(1,'Bundle'),(2,'n x m'),(3,'n x prezzo')], string='Tipo Offerta', default=2,required=True)
    priority = fields.Integer(string="priorità", default = 0)
    qty_selled = fields.Float( string='Quantità venduta', default=0.0)




    @api.one
    @api.constrains('offer_cart_id')
    def _check_priority(self):
        self.priority = self.offer_cart_id[0].priority
        self.offer_type = self.offer_cart_id[0].offer_type   

    @api.one
    @api.constrains('active')
    def _check_active_bundle(self):
        if self.offer_type == 1 and not self.active and  self.offer_cart_id.active:
            self.offer_cart_id.active = False
            for pl in self.offer_cart_id.products_list:
                if pl.id != self.id:
                    pl.active = False
           

           

class BonusOffer(models.Model):     
    _name = "netaddiction.specialoffer.bonus"


    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla",default=True)
    author_id = fields.Many2one(comodel_name='res.users',string='Autore', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_selled = fields.Float( string='Quantità venduta', default=0.0)
    
    
    products_list = fields.One2many('netaddiction.specialoffer.bonus_offer_line', 'bonus_offer_id', string='Lista prodotti')


class BonusOfferLine(models.Model):

    _name = "netaddiction.specialoffer.bonus_offer_line"

    

    active = fields.Boolean(default=True,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    bonus_offer_id = fields.Many2one('netaddiction.specialoffer.bonus', string='Offerta Carrello', index=True, copy=False, required=True)
    qty_selled = fields.Float( string='Quantità venduta', default=0.0)



