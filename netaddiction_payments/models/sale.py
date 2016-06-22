# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api



class Order(models.Model):
    _inherit = 'sale.order'

    payment_method_id = fields.Many2one('account.journal', string='Metodo di pagamento')