# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class CatalogOffer(models.Model):

    _name = "netaddiction.specialoffer.catalog"


    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=True)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    author_id = fields.Many2one(comodel_name='res.users',string='Autore', required=True)
    date_start = fields.Date('Start Date', help="Data di inizio della offerta", required=True)
    date_end = fields.Date('End Date', help="Data di fine dell'offerta", required=True)
    list_prod = fields.One2many(comodel_name='product.product',compute='populate_products')
    priority = fields.Selection([(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], string='Priorità', default=1,required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in unavendibili in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limiite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_min = fields.Integer( string='Quantità minima acquisto', help = "Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.", required=True)
    qty_selled = fields.Integer( string='Quantità venduta', default=0)
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta', default=2,required=True)
    fixed_price = fields.Integer(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")

    #BUG noto: se nella vista scrivi -1 su fixed price  poi cambi a percent discount riesci a scrivere il -1
    #TODO:Non funziona bene nella vista, da sistemare
    
    @api.one
    @api.constrains('fixed_price','offer_type')
    def _check_value(self):
        if self.offer_type == 1 and self.fixed_price <= 0:
            raise ValidationError("Il valore del prezzo fisso non può essere minore  o uguale di zero")

    @api.one
    @api.constrains('percent_discount','offer_type')
    def _check_value(self):
        if self.offer_type == 2 and (self.percent_discount <= 0 or self.percent_discount > 100):
            raise ValidationError("Il valore dello sconto percentuale non può essere minore di 0 o maggiore di 100")


    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_partner_id(self):
       if(self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")

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
    def populate_products(self):
        dom = self.expression_id.find_products_domain()
        ids =[]
        for prod in self.env['product.product'].search(dom):
            ids.append(prod.id)
        self.list_prod = [(6,0,ids)]



class ShoppingCartOffer(models.Model):

    _name = "netaddiction.specialoffer.cart"


    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla",default=True)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione', required=True)
    author_id = fields.Many2one(comodel_name='res.users',string='Autore', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    date_start = fields.Date('Start Date', help="Data di inizio della offerta", required=True)
    date_end = fields.Date('End Date', help="Data di fine dell'offerta", required=True)
    list_prod = fields.One2many(comodel_name='product.product',compute='populate_products')
    priority = fields.Selection([(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], string='Priorità', default=1,required=True)
    qty_max_buyable = fields.Integer( string='Quantità massima acquistabile', help = "Quantità massima di prodotti acquistabili in unavendibili in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer( string='Quantità limite', help = "Quantità limiite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_min = fields.Integer( string='Quantità minima acquisto', help = "Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.", required=True)
    qty_selled = fields.Integer( string='Quantità venduta', default=0)
    offer_type = fields.Selection([(1,'Bundle'),(2,'n x m')], string='Tipo Offerta', default=2,required=True)
    n = fields.Integer(string="N")
    m = fields.Integer(string="M")

    #TODO: N < M, N>0, M>0
    


    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_partner_id(self):
       if(self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")

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
