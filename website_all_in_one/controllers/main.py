# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import json
from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
import werkzeug.urls
import werkzeug.wrappers
import base64
import io
from io import StringIO
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, date
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class OdooWebsiteAllInOne(http.Controller):

	# @http.route('/shop/payment/attachment/add', type='http', auth="public", website=True)
	# def payment_attachment_add(self, url=None, upload=None, **post):
	
	# 	cr, uid, context = request.cr, request.uid, request.context 

	# 	order = request.website.sale_get_order()
					
	# 	Attachments = request.env['ir.attachment']  # registry for the attachment table
		
	# 	upload_file = request.httprequest.files.getlist('upload')
		
	# 	if upload_file:
	# 		for i in range(len(upload_file)):
	# 			attachment_id = Attachments.sudo().create({
	# 				'name': upload_file[i].filename,
	# 				'type': 'binary',
	# 				'datas': base64.b64encode(upload_file[i].read()),
	# 				'store_fname': upload_file[i].filename,
	# 				'public': True,
	# 				'res_model': 'ir.ui.view',
	# 				'sale_order_id' : order.id,
	# 			})   
			
	# 		return request.redirect('/shop/payment')
		
	# @http.route(['/search/suggestion'], type='http', auth="public", website=True)
	# def search_suggestion(self, **post):
	# 	suggestion_list = []
	# 	product=[]
	# 	product_list_name={}        


	# 	if post:
	# 		for suggestion in post.get('query').split(" "):
	# 			product_list = request.env['product.template'].search(([('website_published', '=', True), ('name', "ilike", suggestion)]))
	# 			read_prod = product_list.read(['name','public_categ_ids'])
	# 			suggestion_list = suggestion_list + read_prod
				

	# 	for line in suggestion_list:
	# 		if len(line['public_categ_ids'])==0:
	# 			prod_str=line['name']+ "No category"
	# 			if not prod_str in product_list_name :
	# 				product.append({'product':line['name'],'category':'No category'})

	# 		for pub_cat_ids in line['public_categ_ids']:
	# 			categ_srch= request.env['product.public.category'].search(([('id','=',pub_cat_ids)]))
	# 			categ_read = categ_srch.read(['name'])
	# 			prod_str=line['name']+categ_read[0]['name']
	# 			if not prod_str in product_list_name :
	# 				product.append({'product':line['name'],'category':categ_read[0]['name']})


	# 	data={}
	# 	data['status']=True,
	# 	data['error']=None,
	# 	data['data']={'product':product}
	# 	return json.dumps(data)
		
	# @http.route(['/page/sitemap'], type='http', auth="public", website=True)
	# def odoo_sitemap(self, page=0, category=None, search='', **post):
	# 	cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
		
	# 	return request.render("website_all_in_one.website_sitemap")

	# @http.route('/shop/cart/giftwrap', type='json', auth="public", methods=['POST'], website=True)
	# def shop_cart_giftwrap(self, notes,product, **post):
	# 	cr, uid, context = request.cr, request.uid, request.context
		
	# 	order = request.website.sale_get_order()

	# 	giftwrap = request.env['giftwrap.configuration'].sudo().browse(product)
	  
	# 	order_line_obj = request.env['sale.order.line'].sudo().search([])
	# 	flag = 0
	# 	for i in order_line_obj:
	# 		if i.product_id.id == giftwrap.product_id.id and i.order_id.id == order.id:
	# 			flag = flag + 1

	# 	if flag == 0:
	# 		res = order_line_obj.sudo().create({
	# 			'product_id': giftwrap.product_id.id,
	# 			'name': giftwrap.product_id.name,
	# 			'price_unit': giftwrap.price,
	# 			'order_id': order.id,
	# 			'product_uom':giftwrap.product_id.uom_id.id,
	# 			'name': notes,
	# 		})
		  
	# 	return True

	@http.route('/submit_review/', type='json', auth="public", website=True)
	def submit_review(self, **post):
		account_move_obj = request.env['account.move'].search([('partner_id','=',request.env.user.partner_id.id),('payment_state','=','paid')])
		if not account_move_obj:
			return True
		
				
# class WebsiteSaleAttachment(WebsiteSale):
# 	def _prepare_product_values(self, product, category, search, **kwargs):
# 		values = super(WebsiteSaleAttachment, self)._prepare_product_values(product, category, search, **kwargs)

# 		attachment_obj = request.env['product.attachment']
# 		attachments = attachment_obj.search([('product_tmpl_id', '=', product.id)])
# 		values['attachments'] = attachments
# 		return values

# 	@http.route(['/download/attachment'], type='http', auth="public", website=True)
# 	def download_attachment(self, attachment_id):
# 		cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
# 		attachment = request.env['product.attachment'].sudo().search_read([('id', '=', int(attachment_id))], ["attachment","name"])

# 		if attachment:
# 			attachment = attachment[0]
# 		else:
# 			return redirect('/shop')

# 		data = io.BytesIO(base64.standard_b64decode(attachment["attachment"]))
# 		return http.send_file(data, filename=attachment['name'], as_attachment=True)


# 	@http.route(['/shop/product/comment/<int:product_template_id>'], type='http', auth="public", methods=['POST'], website=True)
# 	def website_product_review(self, product_template_id, **post):
# 		cr, uid, context = request.cr, request.uid, request.context
# 		description=post.get('short_description')
# 		review_rate = post.get('review')
# 		comment = post.get('comment')
# 		account_move_obj = request.env['account.move'].search([('partner_id','=',request.env.user.partner_id.id),('payment_state','=','paid')])
# 		if account_move_obj:
# 			public_category = request.env['product.public.category'].search([('product_tmpl_ids','in',product_template_id)])
# 			if public_category.loyal_for_review:
# 				points = public_category.loyal_for_review
# 			else:
# 				points = public_category.parent_id.loyal_for_review

# 			reviews_ratings = request.env['reviews.ratings'].search([('customer_id','=',uid),('rating_product_id','=',product_template_id)])
# 			if not reviews_ratings:
# 				points += request.env.user.partner_id.loyalty_points
# 				request.env.user.partner_id.write({'loyalty_points':points})
			
# 			reviews_ratings = request.env['reviews.ratings']
# 			reviews_ratings.create({'message_rate':review_rate, 'short_desc':description, 'review':comment, 'website_message':True, 'rating_product_id':product_template_id, 'customer_id':uid})
# 			return werkzeug.utils.redirect( request.httprequest.referrer + "#reviews" )
				
				
# class website_account_payment(CustomerPortal):

# 	@http.route(['/my/invoices/multiple/payment'], type='http', auth="public", website=True)
# 	def multiple_payment(self,**post):
# 		if post:
# 			if post.get('debug'):
# 				return request.render("website_all_in_one.pay_multiple_payment",{'warning':'warning'})
# 			else:
# 				user_id = request.uid
# 				user = request.env['res.users'].browse(user_id)
# 				invoice_obj = request.env['account.move']

# 				invoices = []
# 				id_list = post['invoice']
# 				new_list = id_list.split(',')
# 				invoice_num = ''
# 				total_amount = 0.00
# 				if id_list != '':
# 					for invoice in new_list:
# 						invoice_search = invoice_obj.search([('id','=',int(invoice))])
# 						invoices.append(invoice_search)
# 						invoice_num = invoice_num + invoice_search.name + ','
# 						total_amount = total_amount + invoice_search.amount_residual

# 					currency_id = user.company_id.currency_id.id
# 					currency = request.env['res.currency'].browse(currency_id)
				
# 					acquirer_id = request.env['payment.acquirer'].sudo().search([('company_id', '=', user.company_id.id),('state', '=', 'enabled')])
# 					acquirer = request.env['payment.acquirer'].browse(acquirer_id)
# 					values = {
# 						'acquire_id' : acquirer_id,
# 						'invoices' : invoices,
# 						'invoice_num' : invoice_num,
# 						'total_amount' : float(total_amount),
# 					}
# 					return request.render("website_all_in_one.pay_multiple_payment",values)
# 				else:
# 					return request.render("website_all_in_one.pay_multiple_payment")
				
# 	@http.route(['/my/invoices/multiple/payment/confirm'], type='http', auth="public", website=True)
# 	def multiple_payment_confirm(self, **post):
# 		if post.get('debug'):
# 			return request.render("website_all_in_one.payment_thankyou")
# 		if post:
# 			user_id = request.uid
# 			user = request.env['res.users'].browse(user_id)

# 			currency_id = user.company_id.currency_id.id
# 			currency = request.env['res.currency'].browse(currency_id)
			
# 			acquirer = post['pm_id']
# 			if post.get('reconciled_invoice_ids'):
# 				invoices = post['reconciled_invoice_ids']
# 			else:
# 				invoices = False
# 			num_list = post['invoice_num']
			
# 			invoices = num_list.split(',')
			
# 			amount = post['amount']
# 			new_amount = 0

# 			for invoice in invoices:
				
# 				acquirer_obj = request.env['payment.acquirer']
# 				invoice_obj = request.env['account.move']
# 				reference_obj = request.env['payment.transaction']
# 				acquirer_id = acquirer_obj.sudo().search([('id','=',int(acquirer))])

# 				invoice_id = invoice_obj.sudo().search([('name','=',str(invoice))])
				
# 				reference = reference_obj.sudo()._compute_reference()
# 				if float(amount) != 0.0:
# 					if invoice_id.amount_residual < float(amount):  
# 						new_amount = invoice_id.amount_residual
# 						amount = abs(invoice_id.amount_residual - float(amount))
# 					else:
# 						new_amount = float(amount)
# 						amount = 0.0
# 				else:
# 					return request.render("website_all_in_one.payment_thankyou")

# 				tx_values = {
# 					'acquirer_id': acquirer_id.id,
# 					'reference': reference,
# 					'amount': new_amount,
# 					'currency_id': int(currency_id),
# 					'partner_id': invoice_id.partner_id.id,
# 				}
				
# 				tx = request.env['payment.transaction'].sudo().create(tx_values)
# 				request.session['website_payment_tx_id'] = tx.id

# 				payment = request.env['account.payment']
# 				payment_method = request.env['account.payment.method'].sudo().search([],limit=1)
				
# 				res = payment.sudo().create({
# 							'partner_id':invoice_id.partner_id.id,
# 							'amount': new_amount,
# 							'payment_type':'inbound',
# 							'partner_type':'customer',
# 							'payment_method_id' : payment_method.id,
# 							'journal_id':acquirer_id.journal_id.id,
# 							'date':date.today(),
# 							'ref':invoice_id.name,
# 							'reconciled_invoice_ids':[(6,0,[invoice_id.id])]
# 							})

# 				sequence_code = 'account.payment.customer.invoice'
# 				res.sudo().write({
					
# 					'name': request.env['ir.sequence'].sudo().with_context(ir_sequence_date=res.date).next_by_code(sequence_code),

# 					})
				
# 				invoice_id.has_reconciled_entries = True
# 				invoice_id.sudo().action_invoice_paid()

# 				# pay_confirm = request.env['account.payment'].sudo().search([("ref","=",invoice_id.name)])
# 				pay_confirm = request.env['account.payment.register'].sudo().search([("communication","=",invoice_id.name)])
				
# 				for payment in pay_confirm:
# 					if not payment.state == 'posted':
# 						payment.sudo().action_create_payments()

# 		return request.render("website_all_in_one.payment_thankyou")
		

# 	@http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
# 	def portal_my_invoices(self, page=1, date_begin=None, date_end=None, **kw):
# 		values = self._prepare_portal_layout_values()
# 		partner = request.env.user.partner_id
# 		AccountInvoice = request.env['account.move']

# 		domain = [
# 			('type', 'in', ['out_invoice', 'out_refund']),
# 			('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
# 			('state', 'in', ['draft', 'posted', 'cancel'])
# 		]
# 		#archive_groups = self._get_archive_groups('account.move', domain)
# 		if date_begin and date_end:
# 			domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

# 		# count for pager
# 		invoice_count = AccountInvoice.search_count(domain)
# 		# pager
# 		pager = request.website.pager(
# 			url="/my/invoices",
# 			url_args={'date_begin': date_begin, 'date_end': date_end},
# 			total=invoice_count,
# 			page=page,
# 			step=self._items_per_page
# 		)
# 		# content according to pager and archive selected
# 		invoices = AccountInvoice.search(domain, limit=self._items_per_page, offset=pager['offset'])
		
# 		values.update({
# 			'date': date_begin,
# 			'invoices': invoices,
# 			'page_name': 'invoice',
# 			'pager': pager,
# 			#'archive_groups': archive_groups,
# 			'default_url': '/my/invoices',
# 		})
# 		return request.render("website_all_in_one.bi_portal_my_invoices", values)
		
# 	@http.route(['/my/invoices/partial/<model("account.move"):id>'], type='http', auth="public", website=True)
# 	def pay_partial(self, **post):
		
# 		env = request.env
# 		user = env.user.sudo()
# 		acquire_id = request.env['payment.acquirer'].search([('company_id', '=', user.company_id.id),('state', '=', 'enabled')])
# 		acquire_obj = request.env['payment.acquirer'].browse(acquire_id)

# 		values = {
# 				'id' : post.get('id'),
# 				'invoice' : post.get('invoice'),
# 				'acquire_id' : acquire_id,
# 		}
# 		return request.render("website_all_in_one.pay_portal_payment",values)

	
# 	@http.route(['/my/invoices/partial/confirm'], type='http', auth="public", website=True)
# 	def quote_confirm(self, **post):
# 		if post.get('debug'):
# 			return request.render("website_all_in_one.payment_thankyou")
# 		if post and post.get('invoice'):
# 			user_id = request.uid
# 			user = request.env['res.users'].browse(user_id)

# 			currency_id = user.company_id.currency_id.id
# 			currency = request.env['res.currency'].browse(currency_id)
			
# 			acquirer = post.get('pm_id')
# 			invoice = int(post.get('invoice'))
# 			amount =  post.get('amount1')

# 			acquirer_obj = request.env['payment.acquirer']
# 			invoice_obj = request.env['account.move']
# 			reference_obj = request.env['payment.transaction']
# 			acquirer_id = acquirer_obj.sudo().search([('id','=',int(acquirer))])

# 			invoice_id = invoice_obj.sudo().browse(invoice)
# 			reference = reference_obj.sudo()._compute_reference()  

# 			tx_values = {
# 				'acquirer_id': acquirer_id.id,
# 				'reference': reference,
# 				'amount': float(amount),
# 				'currency_id': int(currency_id),
# 				'partner_id': invoice_id.partner_id.id,
# 			}
			
# 			tx = request.env['payment.transaction'].sudo().create(tx_values)
# 			request.session['website_payment_tx_id'] = tx.id

# 			payment = request.env['account.payment']
# 			payment_method = request.env['account.payment.method'].sudo().search([],limit=1)

# 			res = payment.sudo().create({
# 						'partner_id':invoice_id.partner_id.id,
# 						'amount': amount,
# 						'payment_type':'inbound',
# 						'partner_type':'customer',
# 						'payment_method_id' : payment_method.id,
# 						'journal_id':acquirer_id.journal_id.id,
# 						'date':date.today(),
# 						'ref':invoice_id.name,
# 						'reconciled_invoice_ids':[(6,0,[invoice_id.id])]
# 						})

# 			sequence_code = 'account.payment.customer.invoice'
# 			res.sudo().write({
				
# 				'name': request.env['ir.sequence'].sudo().with_context(ir_sequence_date=res.date).next_by_code(sequence_code),

# 				})
			
# 			invoice_id.has_reconciled_entries = True
# 			invoice_id.sudo().action_invoice_paid()

# 			pay_confirm = request.env['account.payment'].sudo().search([("ref","=",invoice_id.name)])
# 			for payment in pay_confirm:
# 				if not payment.state == 'posted':
# 					payment.sudo().action_post()

# 			return request.render("website_all_in_one.payment_thankyou")

# 	@http.route(['/my/profile'], type='http', auth="public", website=True)
# 	def partner_profile(self, page=1, **kwargs):
# 		values = {}
# 		param = request.env['ir.config_parameter'].sudo()
# 		param.set_param('auth_signup.reset_password', True)
# 		partner = request.env.user.partner_id
# 		shipping_address = request.env['res.partner'].search([['parent_id','=',partner.id],['type','=','delivery']])
# 		billing_address = request.env['res.partner'].search([['parent_id','=',partner.id],['type','=','invoice']])
# 		values.update({'sh_address':shipping_address,'inv_address':billing_address})
# 		return request.render("website_all_in_one.bi_portal_my_profile",values)


# 	@http.route(['/my/profile/edit', '/my/profile/edit/page/<int:page>'], type='http', auth="public", website=True)
# 	def partner_profile_edit(self, page=1, **kwargs):
# 		partner = request.env.user.partner_id
# 		return request.render("website_all_in_one.bi_portal_my_profile_edit")

# 	@http.route(['/my/profile/thankyou'], type='http', auth="public", website=True)
# 	def edit_your_profile(self, **post):
# 		if post.get('debug'):
# 			return request.render("website_all_in_one.profile_thankyou")
# 		pic1 = post['picture']
# 		pic2 = post['current_pic']
# 		if pic1:
# 			pic = base64.encodestring(pic1.read())
# 		else:
# 			pic = pic2
# 		if post['country_id']:
# 			country_id = int(post['country_id'])
# 		else:
# 			country_id = False
# 		if post['name'] and post['street'] and post['company_name']:
# 			name = post['name']
# 			street = post['street']
# 			company_name = post['company_name']
# 		else:
# 			name = False
# 			street = False
# 			company_name = False
# 		if post['city']:
# 			city = post['city']
# 		else:
# 			city = False
# 		if post['function']:
# 			function = post['function']
# 		else:
# 			function = False
# 		if post['zip']:
# 			zipp = post['zip']
# 		else:
# 			zipp = False
# 		if post['street2']:
# 			street2 = post['street2']
# 		else:
# 			street2 = False
# 		if post['phone']:
# 			phone = post['phone']
# 		else:
# 			phone = False
# 		if post['mobile']:
# 			mobile = post['mobile']
# 		else:
# 			mobile = False
# 		if post['email']:
# 			email = post['email']
# 		else:
# 			email = False
# 		if post['state_id']:
# 			state_id = post['state_id']
# 		else:
# 			state_id = False
# 		partner_obj = request.env['res.partner'].sudo().search([('id','=', post['id'])])

# 		for i in partner_obj:
# 			i.update({'name': name,
# 						'city': city,
# 						'function': function,
# 						'zip': zipp,
# 						'street': street,
# 						'street2': street2,
# 						'phone': phone,
# 						'mobile': mobile,
# 						'email': email,
# 						'company_name': company_name,
# 						'state_id': state_id,
# 						'country_id': country_id,
# 						'image_1920': pic,
# 			})
# 		return request.render("website_all_in_one.profile_thankyou")

# 	@http.route(['/my/shipping_address/edit','/my/shipping_address/edit/<int:sh_id>'], type='http', auth="public", website=True)
# 	def partner_shipping_address_edit(self, sh_id = False, **kwargs):
# 		partner = request.env['res.partner'].browse(sh_id)
# 		if partner:
# 			return request.render("website_all_in_one.bi_portal_my_shipping_edit",{'partner':partner,'option':'edit'})
# 		else:
# 			return request.render("website_all_in_one.bi_portal_my_shipping_edit",{'partner':request.env.user.partner_id,'option':'create'})        

# 	@http.route(['/shipping_address/delete/<int:sh_id>'], type='http', auth="public", website=True)
# 	def partner_shipping_address_delete(self, sh_id = False, **kwargs):
# 		partner = request.env['res.partner'].browse(sh_id)
# 		try:
# 			with http.request.env.cr.savepoint():
# 				partner.unlink()
# 				return request.redirect('/my/profile')
# 		except:
# 			return request.redirect('/error_page/shipping')

# 	@http.route(['/shipping_address/thankyou'], type='http', auth="public", website=True)
# 	def edit_your_shipping_address(self, **post): 
# 		if post.get('debug'):
# 			return request.render("website_all_in_one.shipping_address_thankyou")      
# 		shipping_address = request.env['res.partner'].sudo().search([('id','=', post['id']),('type','=','delivery')],limit=1)
# 		if post['country_id']:
# 			country_id = int(post['country_id'])
# 		else:
# 			country_id = False
# 		if post['name'] and post['street']:
# 			name = post['name']
# 			street = post['street']
# 		else:
# 			name = False
# 			street = False
# 		if post['city']:
# 			city = post['city']
# 		else:
# 			city = False
# 		if post['zip']:
# 			zipp = post['zip']
# 		else:
# 			zipp = False
# 		if post['street2']:
# 			street2 = post['street2']
# 		else:
# 			street2 = False
# 		if post['phone']:
# 			phone = post['phone']
# 		else:
# 			phone = False
# 		if post['mobile']:
# 			mobile = post['mobile']
# 		else:
# 			mobile = False
# 		if post['email']:
# 			email = post['email']
# 		else:
# 			email = False
# 		if post['state_id']:
# 			state_id = post['state_id']
# 		else:
# 			state_id = False
# 		if shipping_address:
# 			shipping_address.write({
# 				'name': name,
# 				'city': city,
# 				'zip': zipp,
# 				'street': street,
# 				'street2': street2,
# 				'phone': phone,
# 				'mobile': mobile,
# 				'email': email,
# 				'state_id': state_id,
# 				'country_id': country_id,
# 				})
# 		else:
# 			partner_obj = request.env['res.partner'].sudo().search([('id','=', post['id'])])
# 			shipping_address = partner_obj.child_ids.create({
# 								'type': 'delivery',
# 								'parent_id':partner_obj.id,
# 								'name': name,
# 								'city': city,
# 								'zip': zipp,
# 								'street': street,
# 								'street2': street2,
# 								'phone': phone,
# 								'mobile': mobile,
# 								'email': email,
# 								'state_id': state_id,
# 								'country_id': country_id,
# 							})
# 		return request.render("website_all_in_one.shipping_address_thankyou")    

# 	@http.route(['/my/billing_address/edit','/my/billing_address/edit/<int:bl_id>'], type='http', auth="public", website=True)
# 	def partner_billing_address_edit(self, bl_id = False, **kwargs):
# 		partner = request.env['res.partner'].browse(bl_id)
# 		if partner:
# 			return request.render("website_all_in_one.bi_portal_my_billing_edit",{'partner':partner,'option':'edit'})
# 		else:
# 			return request.render("website_all_in_one.bi_portal_my_billing_edit",{'partner':request.env.user.partner_id,'option':'create'})

# 	@http.route(['/billing_address/delete/<int:bl_id>'], type='http', auth="public", website=True)
# 	def partner_billing_address_delete(self, bl_id = False, **kwargs):
# 		partner = request.env['res.partner'].browse(bl_id)
# 		try:
# 			with http.request.env.cr.savepoint():
# 				partner.unlink()
# 				return request.redirect('/my/profile')
# 		except:
# 			return request.redirect('/error_page/billing')

# 	@http.route(['/billing_address/thankyou'], type='http', auth="public", website=True)
# 	def edit_your_billing_address(self, **post):
# 		if post.get('debug'):
# 			return request.render("website_all_in_one.billing_address_thankyou")
# 		billing_address = request.env['res.partner'].sudo().search([('id','=', post['id']),('type','=','invoice')],limit=1)
# 		if post['country_id']:
# 			country_id = int(post['country_id'])
# 		else:
# 			country_id = False
# 		if post['name'] and post['street']:
# 			name = post['name']
# 			street = post['street']
# 		else:
# 			name = False
# 			street = False
# 		if post['city']:
# 			city = post['city']
# 		else:
# 			city = False
# 		if post['zip']:
# 			zipp = post['zip']
# 		else:
# 			zipp = False
# 		if post['street2']:
# 			street2 = post['street2']
# 		else:
# 			street2 = False
# 		if post['phone']:
# 			phone = post['phone']
# 		else:
# 			phone = False
# 		if post['mobile']:
# 			mobile = post['mobile']
# 		else:
# 			mobile = False
# 		if post['email']:
# 			email = post['email']
# 		else:
# 			email = False
# 		if post['state_id']:
# 			state_id = post['state_id']
# 		else:
# 			state_id = False
# 		if billing_address:
# 			billing_address.write({
# 				'name': name,
# 				'city': city,
# 				'zip': zipp,
# 				'street': street,
# 				'street2': street2,
# 				'phone': phone,
# 				'mobile': mobile,
# 				'email': email,
# 				'state_id': state_id,
# 				'country_id': country_id,
# 				})
# 		else:
# 			partner_obj = request.env['res.partner'].sudo().search([('id','=', post['id'])])
# 			billing_address = partner_obj.child_ids.create({
# 								'type': 'invoice',
# 								'parent_id':partner_obj.id,
# 								'name': name,
# 								'city': city,
# 								'zip': zipp,
# 								'street': street,
# 								'street2': street2,
# 								'phone': phone,
# 								'mobile': mobile,
# 								'email': email,
# 								'state_id': state_id,
# 								'country_id': country_id,
# 							})
# 		return request.render("website_all_in_one.billing_address_thankyou")
		
# 	@http.route(['/error_page/shipping'], type='http', auth="public", website=True)
# 	def error_shipping_address(self, **post):
# 		return request.render("website_all_in_one.error_page",{'address':'shipping'})

# 	@http.route(['/error_page/billing'], type='http', auth="public", website=True)
# 	def error_billing_address(self, **post):
# 		return request.render("website_all_in_one.error_page",{'address':'billing'})

# 	@http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
# 	def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
# 		values = self._prepare_portal_layout_values()
# 		AccountInvoice = request.env['account.move']

# 		domain = [('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),('state','!=','draft')]

# 		searchbar_sortings = {
# 			'date': {'label': _('Invoice Date'), 'order': 'invoice_date desc'},
# 			'duedate': {'label': _('Due Date'), 'order': 'invoice_date_due desc'},
# 			'name': {'label': _('Reference'), 'order': 'name desc'},
# 			'state': {'label': _('Status'), 'order': 'state'},
# 		}
# 		# default sort by order
# 		if not sortby:
# 			sortby = 'date'
# 		order = searchbar_sortings[sortby]['order']

# 		#archive_groups = self._get_archive_groups('account.move', domain)
# 		if date_begin and date_end:
# 			domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

# 		# count for pager
# 		invoice_count = AccountInvoice.search_count(domain)
# 		# pager
# 		pager = portal_pager(
# 			url="/my/invoices",
# 			url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
# 			total=invoice_count,
# 			page=page,
# 			step=self._items_per_page
# 		)
# 		# content according to pager and archive selected
# 		invoices = AccountInvoice.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
# 		request.session['my_invoices_history'] = invoices.ids[:100]

# 		values.update({
# 			'date': date_begin,
# 			'invoices': invoices,
# 			'page_name': 'invoice',
# 			'pager': pager,
# 			#'archive_groups': archive_groups,
# 			'default_url': '/my/invoices',
# 			'searchbar_sortings': searchbar_sortings,
# 			'sortby': sortby,
# 		})
# 		return request.render("account.portal_my_invoices", values)

# 	def _prepare_portal_layout_values(self):
# 		values = super(website_account_payment, self)._prepare_portal_layout_values()
# 		reviewes_ids = request.env['reviews.ratings'].sudo()
# 		if request.env.user.review_and_assign_loyalty_points == True:
# 			reviewes_count = reviewes_ids.sudo().search_count([])
# 			values.update({
# 				'reviewes_count': reviewes_count,
# 			})
# 		return values

	@http.route(['/reviewes', '/reviewes/<int:page>'], type='http', auth="user", website=True)
	def portal_my_reviewes(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
		values = self._prepare_portal_layout_values()
		
		# task count
		reviews_count = request.env['reviews.ratings'].sudo().search_count([])
		# pager
		pager = portal_pager(
			url="/reviewes",
			total=reviews_count,
			page=page,
			step=self._items_per_page
		)
		# content according to pager and archive selected
		
		reviews = request.env['reviews.ratings'].sudo().search([], limit=self._items_per_page, offset=pager['offset'])
		all_reviews = [reviews]

		values.update({
			'date': date_begin,
			'date_end': date_end,
			'all_reviews': all_reviews,
			'page_name': 'reviewes',
			'default_url': '/reviewes',
			'pager': pager,
		})
		return request.render("website_all_in_one.portal_reviewes_view", values)

		
