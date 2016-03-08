# -*- coding: utf-8 -*-
from openerp import models, fields, api


class OffersProducts(models.Model):
    _inherit = 'product.product'

    fake_price = fields.Float(string="Prezzo Falso")
    offer_price = fields.Float(string="Prezzo con offerta applicata", compute='compute_offer_price')

    offer_catalog_lines = fields.One2many('netaddiction.specialoffer.offer_catalog_line', 'product_id', string='offerte catalogo')
    offer_cart_lines = fields.One2many('netaddiction.specialoffer.offer_cart_line', 'product_id', string='offerte carrello')


    @api.one
    def compute_offer_price(self):
    	
    	if self.offer_catalog_lines:
    		
    		curr_off = self.offer_catalog_lines[0]
    		if curr_off:
    			self.offer_price = curr_off.fixed_price if curr_off.offer_type == 1 else (self.final_price - (self.final_price/100)*curr_off.percent_discount)
    		else:
    			self.offer_price =  0.0

    	else:
    		self.offer_price =  0.0

class OffersCatalogSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'



    fixed_price = fields.Integer(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta', default=None)
    offer_author_id = fields.Many2one(comodel_name='res.users',string='Autore offerta')
    offer_name = fields.Char(string='Offerta')
    negate_offer = fields.Boolean(string="Ignora offerta", default=False)




    def _check_offer_validity(self,offer,offer_line,product,uom_quantity):
        """ metodo per controllare la validità dell'offerta
        ritorna True se l'offerta 'offer' è valida per il prodotto 'product' con quantità 'uom_quantity'
        nella offer line 'offer_line'. False altrimenti.
        Se l'offerta  ha superato il limite di oggetti vendibili questa viene spenta, viene avvertito un 
        responsabile tramite mail e l'ordine viene spostato nello stato problema.
        Nel caso di che la offer line abbia più oggetti di quelli massimi consentiti dall'offerta per singolo ordine
        viene lanciata una  QtyMaxBuyableException
        """
        if(offer.date_end > fields.Date.today()):
            if(offer_line.qty_max_buyable > 0 and uom_quantity > offer_line.qty_max_buyable):
                raise QtyMaxBuyableException(product.name, product.id)
                
            if(uom_quantity < offer_line.qty_min):
                #ritorno false e l'offerta non viene applicata
                return False
            #if(offer_line.qty_limit > 0 and offer_line.qty_selled + uom_quantity > offer_line.qty_limit):
                #questa cosa va fatta solo in action confirm!
                #offer_line.qty_selled += uom_quantity
                #TODO: aggiungi notifica (e manda mail a riccardo in action problems)
                #molto importante perchè così quando viene chiamato action_confirm l'ordine viene spostato in problem
                #offer_line.active =False
                #return False
                #pass

            
            return True

        else:
            return False



    @api.multi
    @api.onchange('product_id','negate_offer')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not (self.product_uom and (self.product_id.uom_id.category_id.id == self.product_uom.category_id.id)):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            #controlli offerta catalogo
            
            offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
            if offer_line:
                offer = offer_line.offer_catalog_id
                if not self.negate_offer and self._check_offer_validity(offer,offer_line,self.product_id,self.product_uom_qty):
                    self.offer_type = offer_line.offer_type
                    self.percent_discount = offer_line.percent_discount
                    self.fixed_price = offer_line.fixed_price
                    self.offer_author_id = offer.author_id
                    self.offer_name = offer.name
                    tassa = self.tax_id.amount
                    detax = self.product_id.offer_price / (float(1) + float(tassa/100))
                    deiva = round(detax,2)
                    vals['price_unit'] = deiva
                    

                else:
                    self.offer_price_unit = None
                    self.offer_type = None
                    self.percent_discount = None
                    self.fixed_price = None
                    self.offer_author_id = None
                    self.offer_name = None
                    vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
                    
            else:
                self.offer_price_unit = None
                self.offer_type = None
                self.percent_discount = None
                self.fixed_price = None
                self.offer_author_id = None
                self.offer_name = None
                vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
        self.update(vals)
        return {'domain': domain}


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )



            offer_line = self.product_id.offer_catalog_lines[0] if len(self.product_id.offer_catalog_lines) >0 else None
            if offer_line:
                offer = offer_line.offer_catalog_id
                if not self.negate_offer and self._check_offer_validity(offer,offer_line,self.product_id,self.product_uom_qty):
                    self.offer_type = offer_line.offer_type
                    self.percent_discount = offer_line.percent_discount
                    self.fixed_price = offer_line.fixed_price
                    self.offer_author_id = offer.author_id
                    self.offer_name = offer.name
                    tassa = self.tax_id.amount
                    detax = self.product_id.offer_price / (float(1) + float(tassa/100))
                    deiva = round(detax,2)
                    self.price_unit = deiva
                    

                else:
                    self.offer_price_unit = None
                    self.offer_type = None
                    self.percent_discount = None
                    self.fixed_price = None
                    self.offer_author_id = None
                    self.offer_name = None
                    self.price_unit = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
                    
            else:
                self.offer_price_unit = None
                self.offer_type = None
                self.percent_discount = None
                self.fixed_price = None
                self.offer_author_id = None
                self.offer_name = None
                self.price_unit = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)


    @api.model
    def create(self,values):
        res = super(OffersCatalogSaleOrderLine, self).create(values)
        offer_line = res.product_id.offer_catalog_lines[0] if len(res.product_id.offer_catalog_lines) >0 else None
        if offer_line:
            offer = offer_line.offer_catalog_id
            if not res.negate_offer and self._check_offer_validity(offer,offer_line,res.product_id,res.product_uom_qty):

                res.offer_type = offer_line.offer_type
                res.percent_discount = offer_line.percent_discount
                res.fixed_price = offer_line.fixed_price
                res.offer_author_id = offer.author_id
                res.offer_name = offer.name
                tassa = res.tax_id.amount
                detax = res.product_id.offer_price / (float(1) + float(tassa/100))
                deiva = round(detax,2)
                res.price_unit = deiva
        return res



class QtyMaxBuyableException(ValueError):
    def __init__(self, prod_str, prod_id):
        self.var_name = 'qty_max_buyable'
        self.prod = prod_str
        self.prod_id = prod_id
    def __str__(self):
        s = u"Quantity massima acquistabile in offerta ecceduta %s id: %s " %(self.prod, self.prod_id)
        return s
    def __repr__(self):
        s = u"Quantity massima acquistabile in offerta ecceduta %s id: %s" %(self.prod, self.prod_id)
        return s
