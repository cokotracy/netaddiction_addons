# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Customers(models.Model):
    _inherit = "res.partner"

    is_b2b = fields.Boolean(string="B2B",)

    favorite_payment_method = fields.Many2one('account.journal', string='Metodo di pagamento preferito')

    payment_term_id = fields.Many2one('account.payment.term', string='Termine di pagamento')

