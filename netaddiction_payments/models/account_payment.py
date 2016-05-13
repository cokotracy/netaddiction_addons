from openerp import models, fields, api

class AccountPayment(models.Model):
    """docstring for AccountPayment"""
    _inherit = 'account.payment'

    order_id = fields.Many2one(comodel_name='sale.order', string='Ordine')

class OrderPayment(models.Model):
    """docstring for OrderPayment"""
    _inherit = 'sale.order'

    #collegamento all'ordine
    account_payment_ids = fields.One2many('account.payment','order_id', string='Pagamenti')

    #replica dei dati della cc 
    token = fields.Char(string='Token')
    last_four = fields.Char(string='Indizio')
    month = fields.Integer(string='Mese')
    year =  fields.Integer(string='Anno')
    name = fields.Char(string='Titolare')

