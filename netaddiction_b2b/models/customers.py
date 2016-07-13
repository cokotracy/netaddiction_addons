# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Customers(models.Model):
    _inherit = "res.partner"

    is_b2b = fields.Boolean(string="B2B", compute="_compute_b2b", default="False", search = "_search_b2b")

    favorite_payment_method = fields.Many2one('account.journal', string='Metodo di pagamento preferito')

    payment_term_id = fields.Many2one('account.payment.term', string='Termine di pagamento')

    @api.depends('property_product_pricelist')
    def _compute_b2b(self):
    	# se la pricelist è diversa da quella base di odoo (id=1)
    	# allore possiamo dire che è un cliente b2b
    	for c in self:
    		if c.property_product_pricelist.id != 1 and c.customer:
    			c.is_b2b = True

    def _search_b2b(self,operator,value):
    	if value:
    		return [('property_product_pricelist','!=',1)]
    	else:
    		return [('property_product_pricelist','=',1)]
