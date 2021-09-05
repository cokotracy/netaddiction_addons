# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import http, SUPERUSER_ID
from odoo import _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.payment.controllers.portal import PaymentProcessing

class WebsiteWallet(http.Controller):


	@http.route(['/wallet'], type='http', auth="public", website=True)
	def wallet_balance(self, **post):
		cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
		partner = request.env.user.partner_id
		company_currency = request.website.company_id.currency_id
		web_currency = request.website.get_current_pricelist().currency_id
		price = float(partner.wallet_balance)
		if company_currency.id != web_currency.id:
			new_rate = (price*web_currency.rate)/company_currency.rate
			price = round(new_rate,2)
		return request.render("odoo_website_wallet.wallet_balance",{'wallet':price})


	@http.route(['/add/wallet/balance'], type='http', auth="public", website=True)
	def add_wallet_balance(self, **post):
		cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
		return request.render("odoo_website_wallet.add_wallet_balance")
		
	
	@http.route(['/wallet/balance/confirm'], type='http', auth="public", website=True)
	def wallet_balance_confirm(self, **post):
	
		product = request.website.wallet_product_id
		if product:
			product_id = product.id
			prd_price=0
			company_currency = request.website.company_id.currency_id
			web_currency = request.website.get_current_pricelist().currency_id      
			if company_currency.id != web_currency.id:
				amount = post['amount']
				amount_replace = amount.replace(',', '')
				price = float(amount_replace)
				new_rate = (price*company_currency.rate)/web_currency.rate
				prd_price = new_rate 
			else:
				amount = post['amount']
				amount_replace = amount.replace(',', '')
				prd_price = float(amount_replace)	
			order = request.website.sale_get_order(force_create=1)
			request.env['sale.order.line'].sudo().create({
				"order_id":order.id,
				"product_id":product_id,
				"product_uom_qty":1,
				"price_unit":prd_price,
				"line_wallet_amount" : prd_price,
			})
			product.write({'list_price':post['amount']})
			return request.redirect("/shop/cart")
		else:
			return request.render("odoo_website_wallet.wallet_product_error")
		
	@http.route('/shop/payment/wallet', type='json', auth="public", methods=['POST'], website=True)
	def wallet(self, wallet, **post):
		cr, uid, context = request.cr, request.uid, request.context
		order = request.website.sale_get_order()
		if wallet:
			order.write({
				'is_wallet' : False,
				'amount_total': (order.amount_untaxed + order.amount_tax)
			})
		if wallet == False:
			order.write({'is_wallet' : True})
			web_currency = request.website.get_current_pricelist().currency_id
			wallet_balance = request.website.get_wallet_balance(web_currency)
			if wallet_balance >= order.amount_total:
				order.write({'amount_total': 0.0 })

			if order.amount_total > wallet_balance:
				deduct_amount = order.amount_total - wallet_balance
				order.write({'amount_total': deduct_amount})
		return True


class WebsiteWalletPayment(WebsiteSale):

	@http.route(['/shop/cart'], type='http', auth="public", website=True)
	def cart(self, access_token=None, revive='', **post):
		order = request.website.sale_get_order()
		if order:
			if order.is_wallet == True:
					order.write({'is_wallet' : False})
		return super(WebsiteWalletPayment, self).cart(**post)


	@http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
	def confirm_order(self, **post):
		order = request.website.sale_get_order()
		if order:
			if order.is_wallet == True:
					order.write({'is_wallet' : False})
		return super(WebsiteWalletPayment, self).confirm_order(**post)


	@http.route('/shop/payment/validate', type='http', auth="public", website=True)
	def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
		""" Method that should be called by the server when receiving an update
		for a transaction. State at this point :

		 - UDPATE ME
		"""
		
		if sale_order_id is None:
			order = request.website.sale_get_order()
		else:
			order = request.env['sale.order'].sudo().browse(sale_order_id)
			assert order.id == request.session.get('sale_last_order_id')

		if transaction_id:
			tx = request.env['payment.transaction'].sudo().browse(transaction_id)
			assert tx in order.transaction_ids()
		elif order:
			tx = order.get_portal_last_transaction()
		else:
			tx = None

		if not order or (order.amount_total and not tx):
			return request.redirect('/shop')

		product = request.website.wallet_product_id

		# if payment.acquirer is credit payment provider
		for line in order.order_line:
			if len(order.order_line) == 1:
				if product and  line.product_id.id == product.id:
					wallet_transaction_obj = request.env['website.wallet.transaction']        
					if tx.acquirer_id.need_approval:
						wallet_create = wallet_transaction_obj.sudo().create({ 
							'wallet_type': 'credit', 
							'partner_id': order.partner_id.id, 
							'sale_order_id': order.id, 
							'reference': 'sale_order', 
							'amount': order.order_line.price_unit * order.order_line.product_uom_qty,
							'currency_id': order.pricelist_id.currency_id.id, 
							'status': 'draft' 
						})
					else:
						wallet_create = wallet_transaction_obj.sudo().create({ 
							'wallet_type': 'credit', 
							'partner_id': order.partner_id.id, 
							'sale_order_id': order.id, 
							'reference': 'sale_order', 
							'amount': order.order_line.price_unit * order.order_line.product_uom_qty,
							'currency_id': order.pricelist_id.currency_id.id, 
							'status': 'done' 
						})
						wallet_create.wallet_transaction_email_send() #Mail Send to Customer
						order.partner_id.update({
							'wallet_balance': order.partner_id.wallet_balance + order.order_line.price_unit * order.order_line.product_uom_qty})
					order.with_context(send_email=True).action_confirm()
					request.website.sale_reset()


		if (not order.amount_total and not tx) or tx.state in ['pending', 'done', 'authorized']:
			if (not order.amount_total and not tx):
				# Orders are confirmed by payment transactions, but there is none for free orders,
				# (e.g. free events), so confirm immediately
				order.with_context(send_email=True).action_confirm()
		elif tx and tx.state == 'cancel':
			# cancel the quotation
			order.action_cancel()

		# clean context and session, then redirect to the confirmation page
		request.website.sale_reset()
		if tx and tx.state == 'draft':
			return request.redirect('/shop')

		PaymentProcessing.remove_payment_transaction(tx)
		return request.redirect('/shop/confirmation')


	@http.route(['/shop/confirmation'], type='http', auth="public", website=True)
	def payment_confirmation(self, **post):
		sale_order_id = request.session.get('sale_last_order_id')
		if sale_order_id:
			order = request.env['sale.order'].sudo().browse(sale_order_id)
			if order.is_wallet == True:
				wallet_obj = request.env['website.wallet.transaction']
				partner = request.env['res.partner'].search([('id','=',order.partner_id.id)])      
				wallet_balance = order.partner_id.wallet_balance
				amount_total = (order.amount_untaxed + order.amount_tax)

				company_currency = request.website.company_id.currency_id
				web_currency = order.pricelist_id.currency_id
				price = float(amount_total)

				if company_currency.id != web_currency.id:
					new_rate = (price*company_currency.rate)/web_currency.rate
					price = round(new_rate,2)

				wallet_create = wallet_obj.sudo().create({ 
					'wallet_type': 'debit', 
					'partner_id': order.partner_id.id, 
					'sale_order_id': order.id, 
					'reference': 'sale_order', 
					'amount': price, 
					'currency_id': company_currency.id, 
					'status': 'done' 
				})
				
				if wallet_balance >= price:
					amount = wallet_balance - price
					order.write({'wallet_used':float(amount_total),'wallet_transaction_id':wallet_create.id })
					partner.sudo().write({'wallet_balance':amount})

				if price > wallet_balance:
					p_wlt = request.website.get_wallet_balance(web_currency)
					order.write({'wallet_used':p_wlt,'wallet_transaction_id':wallet_create.id})
					partner.sudo().write({'wallet_balance':0.0})
					order.wallet_transaction_id.update({'amount':p_wlt})
				wallet_create.wallet_transaction_email_send()
				return request.render("website_sale.confirmation", {'order': order})
			else:
				return super(WebsiteWalletPayment, self).payment_confirmation(**post)
		return super(WebsiteWalletPayment, self).payment_confirmation(**post)    



class CustomerPortalWalletTransaction(CustomerPortal):

	
	def _prepare_portal_layout_values(self):
		values = super(CustomerPortalWalletTransaction, self)._prepare_portal_layout_values()
		partner = request.env.user.partner_id
		WalletTransaction = request.env['website.wallet.transaction'].sudo()
		wallet_count = WalletTransaction.sudo().search_count([
			('partner_id', '=', partner.id)])
		values.update({
			'wallet_count': wallet_count,
		})
		return values	
	
	@http.route(['/my/wallet-transactions', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
	def portal_my_wallet_transaction(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
		
		values = self._prepare_portal_layout_values()
		partner = request.env.user.partner_id
		WalletTransaction = request.env['website.wallet.transaction'].sudo()
		domain = [
			('partner_id', '=', partner.id)]
			
		searchbar_sortings = {
			'id': {'label': _('Wallet Transactions'), 'order': 'id desc'},
			
		}
		if not sortby:
			sortby = 'id'
		sort_wallet_transaction = searchbar_sortings[sortby]['order']
		# count for pager
		wallet_count = WalletTransaction.sudo().search_count(domain)
		# make pager
		pager = portal_pager(
			url="/my/wallet-transactions",
			total=wallet_count,
			page=page,
			step=self._items_per_page
		)
		# search the count to display, according to the pager data
		wallets = WalletTransaction.sudo().search(domain, order=sort_wallet_transaction, limit=self._items_per_page, offset=pager['offset'])
		request.session['my_wallet_transaction_history'] = wallets.ids[:100]
		values.update({
			'wallets': wallets.sudo(),
			'page_name': 'wallet',
			'pager': pager,
			'default_url': '/my/subcontractor-job-order',
		})
		return request.render("odoo_website_wallet.portal_my_wallet_transactions", values)
		
		
