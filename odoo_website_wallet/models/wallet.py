# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID

class ResConfigSettingInherit(models.TransientModel):
	_inherit = 'res.config.settings'

	use_wallet = fields.Boolean(string='Use Wallet',related="company_id.use_wallet",readonly=False)
	wallet_product_id = fields.Many2one('product.product',string="Wallet Recharge Product",related="company_id.wallet_product_id", domain="[('type', '=', 'service')]",readonly=False)

class Res_company_inherit(models.Model):
	_inherit = 'res.company'

	use_wallet = fields.Boolean(string='Use Wallet')
	wallet_product_id = fields.Many2one('product.product',string="Wallet Recharge Product", domain="[('type', '=', 'service')]")

class res_partner(models.Model):
	_inherit = 'res.partner'

	wallet_balance = fields.Float('Wallet Balance')
	wallet_transaction_count = fields.Integer(compute='_compute_wallet_transaction_count', string="Wallet")

	def _compute_wallet_transaction_count(self):
		wallet_data = self.env['pos.wallet.transaction'].search([('partner_id', 'in', self.ids)])
		partner.wallet_balance = 0.0
		for partner in self:
			for trns in wallet_data : 
				if trns.status == 'done' :
					if trns.wallet_type == 'credit' :
						partner.wallet_balance += float(trns.amount)

					if trns.wallet_type == 'debit' :
						partner.wallet_balance -= float(trns.amount)

			partner.wallet_transaction_count = len(wallet_data)

	def action_view_wallet_trans(self):
		return {
			'name': 'Wallet Transactions Details',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'website.wallet.transaction',
			'domain': [('partner_id', '=', self.id)],
		}

class account_move(models.Model):
	_inherit = 'account.move'

	wallet_added = fields.Boolean(string='Wallet Added')

		
class website_wallet_transaction(models.Model):
	_name='website.wallet.transaction'
	
	#============================================== mail send ===========================================
	
	def wallet_transaction_email_send(self):
		context = self._context
		active_ids = context.get('active_ids')
		sale_manager_id = self.env['ir.model.data'].sudo().get_object_reference('sales_team','group_sale_manager')[1]
		group_manager = self.env['res.groups'].sudo().browse(sale_manager_id)
		template_id = ''
		manager = ''
		if group_manager.users:
			manager = group_manager.users[0]
		
		if self.wallet_type == 'credit':
			template_id = self.env['ir.model.data'].get_object_reference('odoo_website_wallet', 'email_template_wallet_transaction_credit')[1]
		else:
			template_id = self.env['ir.model.data'].get_object_reference('odoo_website_wallet', 'email_template_wallet_transaction_debit')[1]
		
		email_template_obj = self.env['mail.template'].browse(template_id)
		# values = email_template_obj.generate_email(self.id)
		# values['email_from'] = manager.partner_id.email
		# values['email_to'] = self.partner_id.email
		# values['author_id'] = manager.partner_id.id
		# values['res_id'] = self.id
		# mail_mail_obj = self.env['mail.mail']
		# msg_id = mail_mail_obj.create(values)
		# if msg_id:
		# 	mail_mail_obj.send([msg_id])
		if email_template_obj:
			email_template_obj.sudo().send_mail(self.id, force_send=True)
		return True
	
	#====================================================================================================

	@api.model
	def create(self, vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('website.wallet.transaction') or 'New'
		res = super(website_wallet_transaction, self).create(vals)
		res.total_amount = res.amount
		if res.wallet_type == 'debit':
			res.debit_amount = -res.total_amount
		else:
			res.debit_amount = 0
		if res.wallet_type == 'credit':
			res.credit_amount = res.amount
		else:
			res.credit_amount = 0
		res.amount_total = res.credit_amount + res.debit_amount
		return res
		
	name = fields.Char('Name')
	wallet_type = fields.Selection([
		('credit', 'Credit'),
		('debit', 'Debit')
		], string='Type', default='credit')
	partner_id = fields.Many2one('res.partner', 'Customer')
	sale_order_id = fields.Many2one('sale.order', 'Sale Order')
	reference = fields.Selection([
		('manual', 'Manual'),
		('sale_order', 'Sale Order')
		], string='Reference', default='manual')
	amount = fields.Char('Amount')
	amount_total = fields.Float('Total Amount')
	total_amount = fields.Float('total')
	credit_amount = fields.Float('Credit Amount')
	debit_amount = fields.Float('Debit Amount')
	currency_id = fields.Many2one('res.currency', 'Currency')
	status = fields.Selection([
		('draft', 'Draft'),
		('done', 'Done')
		], string='Status', readonly=True, default='draft')

	def approve_button(self):
		for transaction in self:
			transaction.wallet_transaction_email_send() #Mail Send to Customer
			balance = transaction.partner_id.wallet_balance + float(transaction.amount)
			transaction.partner_id.write({'wallet_balance': balance})
			transaction.write({'status' : 'done'})


class Website(models.Model):
	_inherit = 'website'

	wallet_product_id = fields.Many2one('product.product',string="Wallet Recharge Product",related="company_id.wallet_product_id", domain="[('type', '=', 'service')]",readonly=False)
		
	def get_wallet_balance(self,web_currency):   
		partner = self.env.user.partner_id
		company_currency = self.company_id.currency_id
		price = float(partner.wallet_balance)
		if company_currency.id != web_currency.id:
			new_rate = (price*web_currency.rate)/company_currency.rate
			price =  round(new_rate,2)
		return price  
	

class PaymentAcquirer(models.Model):
	_inherit = 'payment.acquirer'

	need_approval = fields.Boolean(string='Need approval')
	website_order_msg = fields.Selection([ ('confirm', 'Confirm Quotation'),
	('invoice', 'Create Invoice'),
	('validate', 'Validate Invoice'),
	('payment', 'Create Payment')], string="Website Order Configuration")
			
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
