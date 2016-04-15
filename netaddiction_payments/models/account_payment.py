from openerp import models, fields, api

class AccountPayment(models.Model):
	"""docstring for AccountPayment"""
	_inherit = 'account.payment'
	
	order_id = fields.Many2one(comodel_name='sale.order', string='Ordine')

class OrderPayment(models.Model):
	"""docstring for OrderPayment"""
	_inherit = 'sale.order'

	account_payment_ids = fields.One2many('account.payment','order_id', string='Pagamenti')