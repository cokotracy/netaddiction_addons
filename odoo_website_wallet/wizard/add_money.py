# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, time, datetime

class AddMoney(models.Model):
	_name = "add.money"
	_description = "Add Money"

	add_amount = fields.Float('Amount',required="True")
	
	def wallet_transaction_email_send(self):
		context = self._context
		active_ids = context.get('active_ids')
		active_id = self.env.context.get('active_ids')
		user_id = self.env['res.users'].browse(active_id)
		
		sale_manager_id = self.env['ir.model.data'].sudo().get_object_reference('sales_team','group_sale_manager')[1]
		group_manager = self.env['res.groups'].sudo().browse(sale_manager_id)
		template_id = ''
		manager = ''
		if group_manager.users:
			manager = group_manager.users[0]
		
		template_id = self.env['ir.model.data'].get_object_reference('odoo_website_wallet', 'email_template_wallet_transaction_credit_khush')[1]
		
		email_template_obj = self.env['mail.template'].browse(template_id)
		#values = email_template_obj.generate_email(self.id)
		#values['email_from'] = manager.partner_id.email
		for user in user_id:
			# values['email_to'] = user.partner_id.email
			# values['author_id'] = manager.partner_id.id
			# values['res_id'] = self.id
			# mail_mail_obj = self.env['mail.mail']
			# msg_id = mail_mail_obj.create(values)
			# if msg_id:
			# 	mail_mail_obj.send([msg_id])

			if email_template_obj:
				email_template_obj.sudo().send_mail(self.id, force_send=True)
													 
		return True

	def add_money_to_wallet(self):
		self.wallet_transaction_email_send()
		active_id = self.env.context.get('active_ids')
		user_id = self.env['res.users'].browse(active_id)
		wallet_transaction_obj = self.env['website.wallet.transaction']
		account_payment_obj = self.env['account.payment']
		for users in user_id:
			balance = users.partner_id.wallet_balance
			balance = balance + self.add_amount
			customer_id = self.env['res.partner'].search([('id','=',users.partner_id.id)])
			customer_id.write({'wallet_balance':balance})
			value = {
			'wallet_type' : 'credit',
			'reference' : 'manual',
			'amount' : self.add_amount,
			'partner_id': users.partner_id.id,
			'currency_id' : users.partner_id.property_product_pricelist.currency_id.id,
			'status' : 'done'
			}
			wallet_obj = wallet_transaction_obj.sudo().create(value)

			date_now = datetime.strftime(datetime.now(), '%Y-%m-%d')
		
			vals = {}
			
			vals = {
				'name' : self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
				'payment_type' : "inbound",
				'amount' : self.add_amount,
				'ref' : "Wallet Recharge",
				'date' : datetime.now().date(),
				'journal_id' : 7,
				'payment_method_id': 1,
				'partner_type': 'customer',
				'partner_id': users.partner_id.id,
			}
			payment_create = account_payment_obj.sudo().create(vals)
			

class AddPayment(models.Model):
	_name = "add.payment"
	_description = "Add Money"

	def wallet_transaction_email_send(self):
		context = self._context
		active_ids = context.get('active_ids')
		active_id = self.env.context.get('active_ids')
		wallet_id = self.env['website.wallet.transaction'].browse(active_id)
		
		sale_manager_id = self.env['ir.model.data'].sudo().get_object_reference('sales_team','group_sale_manager')[1]
		group_manager = self.env['res.groups'].sudo().browse(sale_manager_id)
		template_id = ''
		manager = ''
		if group_manager.users:
			manager = group_manager.users[0]
		
		template_id = self.env['ir.model.data'].get_object_reference('odoo_website_wallet', 'email_template_wallet_transaction_credit_payment')[1]
		
		email_template_obj = self.env['mail.template'].browse(template_id)
		#values = email_template_obj.generate_email(self.id)
		#values['email_from'] = manager.partner_id.email
		for wallet in wallet_id:
			# values['email_to'] = wallet.partner_id.email
			# values['author_id'] = manager.partner_id.id
			# values['res_id'] = self.id
			# mail_mail_obj = self.env['mail.mail']
			# msg_id = mail_mail_obj.create(values)
			# if msg_id:
			# 	mail_mail_obj.send([msg_id.id])

			if email_template_obj:
				email_template_obj.sudo().send_mail(self.id, force_send=True)
													 
		return True

	def add_money_to_wallet(self):
		self.wallet_transaction_email_send()
		active_id = self.env.context.get('active_ids')
		wallet_id = self.env['website.wallet.transaction'].browse(active_id)
		for wallet in wallet_id:
			if wallet.wallet_type == 'debit':
				raise UserError(
				_('You can not approve wallet transaction of type debit.'))
			
			elif wallet.status == 'done':
				raise UserError(
				_('You can not approve wallet transaction of done state.'))

			else:
				balance = wallet.partner_id.wallet_balance
				balance = balance + wallet.amount_total
				customer_id = self.env['res.partner'].search([('id','=',wallet.partner_id.id)])
				customer_id.write({'wallet_balance':balance})
				wallet.status = 'done'
