from openerp import models, fields, api

class AccountPayment(models.Model):
    """docstring for AccountPayment"""
    _inherit = 'account.payment'

    order_id = fields.Many2one(comodel_name='sale.order', string='Ordine')

    #replica dei dati della cc 
    cc_token = fields.Char(string='Token')
    cc_last_four = fields.Char(string='Indizio')
    cc_month = fields.Integer(string='Mese')
    cc_year =  fields.Integer(string='Anno')
    cc_name = fields.Char(string='Titolare')
    cc_status = fields.Selection([('init','Da autorizzare'),('auth','Autorizzato'),('commit','Pagato')])

class OrderPayment(models.Model):
    """docstring for OrderPayment"""
    _inherit = 'sale.order'

    #collegamento all'ordine
    account_payment_ids = fields.One2many('account.payment','order_id', string='Pagamenti')


