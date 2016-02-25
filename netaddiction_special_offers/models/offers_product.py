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

    offer_price_unit = fields.Float(default=None, string='Prezzo Offerta',compute='_compute_offer_unit',readonly=True, store=True)

    fixed_price = fields.Integer(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    offer_type = fields.Selection([(1,'Prezzo Fisso'),(2,'Percentuale')], string='Tipo Offerta')
    offer_author_id = fields.Many2one(comodel_name='res.users',string='Autore offerta')
    offer_name = fields.Char(string='Offerta')
    negate_offer = fields.Boolean(string="Ignora offerta", default=False)


    @api.multi
    @api.depends('product_id','product_uom_qty','negate_offer')
    def _compute_offer_unit(self):
        for line in self:

            offer_line = line.product_id.offer_catalog_lines[0] if len(line.product_id.offer_catalog_lines) >0 else None
            if offer_line:
                offer = offer_line.offer_catalog_id
                if not self.negate_offer and self._check_offer_validity(offer,offer_line,line.product_id,line.product_uom_qty):
                    line.offer_type = offer_line.offer_type
                    line.percent_discount = offer_line.percent_discount
                    line.fixed_price = offer_line.fixed_price
                    line.offer_author_id = offer.author_id
                    line.offer_name = offer.name
                    line.offer_price_unit = line.product_id.offer_price

                else:
                    line.offer_price_unit = None
                    line.offer_type = None
                    line.percent_discount = None
                    line.fixed_price = None
                    line.offer_author_id = None
                    line.offer_name = None
                    
            else:
                line.offer_price_unit = None
                line.offer_type = None
                line.percent_discount = None
                line.fixed_price = None
                line.offer_author_id = None
                line.offer_name = None

    def _check_offer_validity(self,offer,offer_line,product,uom_quantity):
        if(offer.date_end > fields.Date.today()):
            if(offer_line.qty_max_buyable > 0 and uom_quantity > offer_line.qty_max_buyable):
                raise QtyMaxBuyableException(product.name)
                
            if(uom_quantity < offer_line.qty_min):
                #ritorno false e l'offerta non viene applicata
                return False
            if(offer_line.qty_limit > 0 and offer_line.qty_selled + uom_quantity > offer_line.qty_limit):
                offer_line.qty_selled += uom_quantity
                #TODO: aggiungi notifica (e manda mail a riccardo in action problems)
                #molto importante perchè così quando viene chiamato action_confirm l'ordine viene spostato in problem
                offer_line.active =False
                return False

            
            return True

        else:
            return False

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','offer_price_unit','negate_offer')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if(not line.offer_price_unit or line.negate_offer ):
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            else:

                tassa = line.tax_id.amount

                detax = line.offer_price_unit / (float(1) + float(tassa/100))
                deiva = round(detax,2)
                taxes = line.tax_id.compute_all(deiva, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })


# class OffersCatalogSaleOrder(models.Model):
#     _inherit = 'sale.order'

    # @api.depends('order_line.price_total','order_line.offer_price')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the SO with offer price
    #     """
    #     for order in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal if line.offer_price is None else line.offer_price
    #             amount_tax += line.price_tax
    #         order.update({
    #             'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
    #             'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
    #             'amount_total': amount_untaxed + amount_tax,
    #         })


class QtyMaxBuyableException(ValueError):
    def __init__(self, value):
        self.var_name = 'qty_max_buyable'
        self.prod = value
    def __str__(self):
        return "Quantità massima acquistabile in offerta ecceduta %s" %self.prod
