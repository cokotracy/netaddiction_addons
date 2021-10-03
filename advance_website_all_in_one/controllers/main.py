# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import werkzeug
import json
from odoo import SUPERUSER_ID, http, tools, _
from odoo.http import request
from datetime import datetime, timedelta, date
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import UserError
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.tools import groupby as groupbyelem
from operator import itemgetter

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

class AdvanceCartSetting(WebsiteSale):

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        
        res_config_obj = request.env['res.config.settings']
        redirect_opt = res_config_obj.sudo().search([], limit=1, order="id desc").redirect_opt
        subtotal_of_orderline = res_config_obj.sudo().search([], limit=1, order="id desc").subtotal_of_orderline
        
        return_url = ''
        if redirect_opt and redirect_opt == 'same':
            path = request.httprequest.headers.environ.get("HTTP_REFERER")
            if path and 'shop' in str(path):
                if path.split('/shop')[1]:
                    return_url = request.redirect(request.httprequest.headers.environ.get("HTTP_REFERER"))
                elif not path.split('/shop')[1]:
                    return_url = request.redirect("/shop")
            else:
                return_url = request.redirect("/shop/cart")
        elif redirect_opt == 'cart':
            return_url = request.redirect("/shop/cart")
        else:
            if kw.get('express'):
                return request.redirect("/shop/checkout?express=1")

            return request.redirect("/shop/cart")

        return return_url

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):

        order = request.website.sale_get_order()
        cart_total = order.amount_total
        
        res_config_obj = request.env['res.config.settings']
        min_cart_value = res_config_obj.sudo().search([], limit=1, order="id desc").min_cart_value

        if float(min_cart_value) > float(cart_total):
            return request.redirect("/shop/cart?error_msg=%s" % _('Minimum cart amount is %s and your current order amount %s.') % (min_cart_value,cart_total))

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            return request.redirect('/shop/address')

        for f in self._get_mandatory_billing_fields():
            if not order.partner_id[f]:
                return request.redirect('/shop/address?partner_id=%d' % order.partner_id.id)

        values = self.checkout_values(**post)

        if post.get('express'):
            return request.redirect('/shop/confirm_order')

        values.update({'website_sale_order': order})

        # Avoid useless rendering if called in ajax
        if post.get('xhr'):
            return 'ok'
        return request.render("website_sale.checkout", values)

    @http.route(['/get-loyalty-points'], type='http', auth='public', website=True)
    def get_loyalty_points(self , **post):
        so = request.env['sale.order'].sudo().browse(int(post.get('order_id')))
        today_date = datetime.today().date() 
        config = request.env['web.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
                            ('expiry_date', '>=', today_date )])
        redeem_value = 0.0
        loyalty_amount = 0.0
        partner = so.partner_id
        company_currency = request.website.company_id.currency_id
        web_currency = request.website.get_current_pricelist().currency_id
        if so:
            for rule in config.redeem_ids:
                if rule.min_amt <= partner.loyalty_points  and   partner.loyalty_points <= rule.max_amt :
                    redeem_value = rule.reward_amt

            if company_currency.id != web_currency.id:
                new_redeem = (redeem_value*web_currency.rate)/company_currency.rate
                redeem_value = round(new_redeem,2)
            
            loyalty_amount = round(redeem_value * partner.loyalty_points ,2)

            data ={
                'partner' : partner.name,
                'points' : partner.loyalty_points,
                'loyalty_amount' : loyalty_amount,
                'redeem_value' : redeem_value,
                'amount_total' : so.amount_total,
                'order_redeem_points' : so.order_redeem_points
            }
            return json.dumps(data)

    @http.route(['/redeem-loyalty-points'], type='http', auth='public', website=True)
    def redeem_loyalty_points(self , **post):
        so = request.env['sale.order'].sudo().browse(int(post.get('order_id')))
        today_date = datetime.today().date() 
        config = request.env['web.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
                            ('expiry_date', '>=', today_date )])
        partner = so.partner_id
        if config:
            res = request.env['sale.order.line'].sudo().create({
                'product_id': config.product_id.id,
                'name': config.product_id.name,
                'price_unit': -int(post.get('entered_points')) * float(post.get('redeem_value')),
                'order_id': so.id,
                'product_uom':config.product_id.uom_id.id,
                'discount_line':True,
                'redeem_points' : int(post.get('entered_points'))
            })
            so.sudo().write({
                'order_redeem_points' :  int(post.get('entered_points')) ,
                'redeem_value' : float(post.get('redeem_value')),
            })
            partner.sudo().write({
                'loyalty_points' : partner.loyalty_points - int(post.get('entered_points'))
                })
            return json.dumps(res.id)


    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        """This route is called when changing quantity from the cart or adding
        a product from the wishlist."""
        so_line = request.env['sale.order.line'].sudo().browse(line_id)
        if so_line.discount_line and set_qty == 0:
            partner = so_line.order_id.partner_id
            partner.sudo().write({
                'loyalty_points' : partner.loyalty_points + so_line.redeem_points
                })
            so_line.order_id.sudo().write({
                'order_redeem_points' :  0
            })

        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}

        value = order._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)

        if not order.cart_quantity:
            order.voucher_code = ''
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity
        
        if not display:
            return value

        value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'date': date.today(),
            'suggested_products': order._cart_accessories()
        })
        value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
            'website_sale_order': order,
        })
        return value

    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
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

        today_date = datetime.today().date() 
        config = request.env['web.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
                            ('expiry_date', '>=', today_date )])
        loyalty_history_obj = request.env['web.loyalty.history']
        
        if not request.website.is_public_user():
            if config:
                credit = request.website.sudo().get_loyalty_balance(order)[0]
                if order.order_redeem_points > 0:
                    vals = {
                        'order_id':order.id,
                        'partner_id': order.partner_id.id,
                        'date' : datetime.now(),
                        'transaction_type' : 'debit',
                        'points': order.order_redeem_points
                    }
                    loyalty_history = loyalty_history_obj.sudo().create(vals)

                if credit > 0 :
                    vals = {
                        'order_id':order.id,
                        'partner_id': order.partner_id.id,
                        'date' : datetime.now(),
                        'transaction_type' : 'credit',
                        'points': credit
                    }
                    loyalty_history = loyalty_history_obj.sudo().create(vals)
                    order.write({'order_credit_points': credit})
                    order.partner_id.sudo().write({
                        'loyalty_points' : order.partner_id.loyalty_points + order.order_credit_points
                    })


        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        list_of_order_product = []
        voucher_id = False
        
        if order.voucher_code:
            voucher_obj_by_name = request.env['web.gift.coupon'].search([('name', '=ilike', order.voucher_code)])
            voucher_obj_by_code = request.env['web.gift.coupon'].search([('c_barcode', '=', order.voucher_code)])
            if voucher_obj_by_name:
                dic = {'code':voucher_obj_by_name,'order':order}
                self._apply_coupon(dic)

            if voucher_obj_by_code:
                dic = {'code':voucher_obj_by_code,'order':order}
                self._apply_coupon(dic)

        if tx.acquirer_id.provider == 'cod':
            payment_acquirer_obj = request.env['payment.acquirer'].sudo().search([('id','=', tx.acquirer_id.id)]) 
        
            order = request.website.sale_get_order()
            product_obj = request.env['product.product'].browse()
            extra_fees_product = request.env['ir.model.data'].get_object_reference('advance_website_all_in_one', 'product_product_fees')[1]
            product_ids = product_obj.sudo().search([('product_tmpl_id.id', '=', extra_fees_product)])
            
            order_line_obj = request.env['sale.order.line'].sudo().search([])
            
            
            flag = 0
            for i in order_line_obj:
                if i.product_id.id == product_ids.id and i.order_id.id == order.id:
                    flag = flag + 1
            
            if flag == 0:
                order_line_obj.sudo().create({
                        'product_id': product_ids.id,
                        'name': 'Extra Fees',
                        'price_unit': payment_acquirer_obj.delivery_fees,
                        'order_id': order.id,
                        'product_uom':product_ids.uom_id.id,
                    
                    })
                tx.update({
                    'fees' : payment_acquirer_obj.delivery_fees,
                    })              
            
            order.with_context(send_email=True).action_confirm()
            request.website.sale_reset()
            return request.render("website_sale.confirmation", {'order': order})

        if 'wallet_product_id' in request.env['website']._fields:
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
        else:
            if order and not order.amount_total and not tx:
                order.with_context(send_email=True).action_confirm()
                return request.redirect(order.get_portal_url())

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

    def _apply_coupon(self,arg):
        partner_record_id = request.env['res.users'].browse(request._uid).partner_id.id
        coupon = arg['code']
        order = arg['order']
        discount_value = 0
        if coupon.amount_type == 'fix':
                discount_value = coupon.amount
        elif coupon.amount_type == 'per':
            total = 0
            for i in order.order_line:
                if i.discount_line == False:
                    total += i.price_subtotal
            discount_value = ((total * coupon.amount)/100)
        coupon.update({
            'coupon_count': (coupon.coupon_count + 1),
            'max_amount':coupon.max_amount - discount_value,
        })
        order.write({
            'sale_coupon_id': coupon.id
        })
        used_sale_coup_id = coupon.sudo().sale_order_ids.sudo().browse(order.id).sale_coupon_id.id
        curr_vouch_id = coupon.id

        if used_sale_coup_id == curr_vouch_id:
            coupon.sale_order_ids.sudo().update({
                'user_id': http.request.env.context.get('uid'),
            })


class PortalLoyaltyHistory(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PortalLoyaltyHistory, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        LoyaltyHistory = request.env['web.loyalty.history'].sudo()
        loyalty_count = LoyaltyHistory.sudo().search_count([
            ('partner_id', '=', partner.id)])
        values.update({
            'loyalty_count': loyalty_count,
        })
        return values   
    
    @http.route(['/my/loyalty/history', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_loyalty_history(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        LoyaltyHistory = request.env['web.loyalty.history'].sudo()
        domain = [
            ('partner_id', '=', partner.id)]
            
        searchbar_sortings = {
            'id': {'label': _('Loyalty History'), 'order': 'id desc'},
            
        }
        if not sortby:
            sortby = 'id'
        sort_loyalty = searchbar_sortings[sortby]['order']
        # count for pager
        loyalty_count = LoyaltyHistory.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/loyalty/history",
            total=loyalty_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        loyalty_points = LoyaltyHistory.sudo().search(domain, order=sort_loyalty, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'loyalty_points': loyalty_points.sudo(),
            'page_name': 'loyalty_points',
            'pager': pager,
            'default_url': '/my/loyalty/history',
        })
        return request.render("advance_website_all_in_one.portal_loyalty_history", values)

        
class WebsiteSale(http.Controller):

    _accept_url = '/cod/payment/feedback'

    @http.route(['/cod/payment/feedback'], type='http', auth='none', csrf=False)
    def cod_form_feedback(self, **post):
        post.update({ 'return_url':'/shop/payment/validate' })
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        
        request.env['payment.transaction'].sudo().form_feedback(post, 'cod')
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
    
    
    @http.route('/shop/payment/cod', type='json', auth="public", methods=['POST'], website=True)
    def codline(self, payment_id, **post):
        return True
    
    @http.route('/shop/payment/default', type='json', auth="public", methods=['POST'], website=True)
    def payment_default(self, payment_id, **post):      
        
        cr, uid, context = request.cr, request.uid, request.context
        
        return request.redirect('/shop/payment/validate')

    @http.route(['/shop/voucher'], type='json', auth="public", methods=['POST'], website=True)
    def voucher_code(self, promo, **post):
        request.env.uid = 1
        current_sale_order = request.website.sale_get_order()

        for i in  current_sale_order.order_line:
            if i.voucher_line == True:
                return "A Voucher is already applied. Please remove it from cart to apply new Voucher."
        dv = False
        by_name = request.env['web.gift.coupon'].search([('name', '=ilike', promo)])
        by_code = request.env['web.gift.coupon'].search([('c_barcode','=', promo)])
        if by_name:
            dv = by_name
            for i in  current_sale_order.order_line:
                if i.product_id.categ_id not in dv.product_categ_ids:
                    return "Can not use coupon for '%s' category products." %(i.product_id.categ_id.display_name)
                if i.product_id in dv.product_ids:
                    return "Can not use coupon for product '%s'." %(i.product_id.name)
        if by_code:
            dv = by_code
            for i in current_sale_order.order_line:
                if i.product_id.categ_id not in dv.product_categ_ids:
                    return "Can not use coupon for '%s' category products." %(i.product_id.categ_id.display_name)
                if i.product_id.product_tmpl_id in dv.product_ids:
                    return "Can not use coupon for product '%s'." %(i.product_id.name)
        if not dv:
            return "Invalid Voucher !"
        else:   
            dv = request.env['web.gift.coupon'].browse(dv).id
            dt_end = False
            discount_value = False
            order_line_obj = request.env['sale.order.line'].sudo().search([])

            if dv.coupon_count >= dv.coupon_apply_times :
                return "Can not use coupon because you reached the maximum limit of usage."

            if dv.amount_type == 'fix':
                discount_value = dv.amount
            elif dv.amount_type == 'per':
                total = 0
                for i in current_sale_order.order_line:
                    if i.discount_line == False:
                        total += i.price_subtotal
                discount_value = ((total * dv.amount)/100)

            if dv.exp_dat_show:
                dt_end = datetime.strptime(str(dv.expiry_date), '%Y-%m-%d %H:%M:%S').date()

            if not dv.max_amount >= discount_value:
                return "Discount amount is higher than maximum amount of this coupon."

            if not current_sale_order.amount_total >= discount_value:
                return "Can not apply discount more than order total."               

            if dv.partner_true == True:
                partner = dv.partner_id.id
                curr_user_partner = request.env['res.users'].browse(request._uid).partner_id
                selected_partner = request.env['res.partner'].browse(partner)
                
                flag = False
                if curr_user_partner.id == selected_partner.id:
                    if dv.exp_dat_show:
                        if dt_end < datetime.now().date():
                            return "This code has been Expired !"
                    res = order_line_obj.sudo().create({
                            'product_id': dv.product_id.id,
                            'name': dv.product_id.name,
                            'price_unit': -discount_value,
                            'order_id': current_sale_order.id,
                            'product_uom':dv.product_id.uom_id.id,
                            'discount_line':True,
                            'voucher_line' : True
                    })
                    current_sale_order.sale_coupon_id = dv
                    current_sale_order.assign_voucher_code(promo)    
                    return True   
                else:
                    return "Invalid Customer !"                  
                                                
            if dv.exp_dat_show:
                if dt_end < datetime.now().date():
                    return "This code has been Expired !"

            res = order_line_obj.sudo().create({
                            'product_id': dv.product_id.id,
                            'name': dv.product_id.name,
                            'price_unit': -discount_value,
                            'order_id': current_sale_order.id,
                            'product_uom':dv.product_id.uom_id.id,
                            'discount_line':True,
                            'voucher_line' : True
                    })
            current_sale_order.sale_coupon_id = dv
            current_sale_order.assign_voucher_code(promo) 
            return True

    def _get_compute_currency_and_context(self, product=None):
        pricelist_context, pricelist = self._get_pricelist_context()
        compute_currency = self._get_compute_currency(pricelist, product)
        return compute_currency, pricelist_context, pricelist

    def _get_pricelist_context(self):
        pricelist_context = dict(request.env.context)
        pricelist = False
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

        return pricelist_context, pricelist

    def _get_compute_currency(self, pricelist, product=None):
        company = product and product._get_current_company(pricelist=pricelist, website=request.website) or pricelist.company_id or request.website.company_id
        from_currency = (product or request.env['res.company']._get_main_company()).currency_id
        to_currency = pricelist.currency_id
        return lambda price: from_currency._convert(price, to_currency, company, fields.Date.today())

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        return 'is_published desc,%s , id desc' % post.get('order', 'website_sequence desc')

    def _get_search_domain(self, search, category, attrib_values, filter_values, brand_set):
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', '|',('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch),
                    ('brand_id.name', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]


        if filter_values:
            filter = None
            ids = []
            for value in filter_values:
                if not filter:
                    filter = value[0]
                    ids.append(value[1])
                elif value[0] == filter:
                    ids.append(value[1])
                else:
                    domain += [('filter_ids.filter_value_ids', 'in', ids)]
                    filter = value[0]
                    ids = [value[1]]
            if filter:
                domain += [('filter_ids.filter_value_ids', 'in', ids)]

        if brand_set:
            brand = None
            ids = []
            for value in brand_set:
                ids.append(value)
                domain += [('brand_id', 'in', ids)]

        return domain

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    # @http.route([
    #     '''/shop''',
    #     '''/shop/page/<int:page>''',
    #     '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
    #     '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>''',
    #     '''/shop/category/<abc>''',
    #     '''/shop/category/page/<int:page>/<abc>'''
    # ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    # def shop(self, page=0, category=None, abc=None, search='', ppg=False, **post):
    #     add_qty = int(post.get('add_qty', 1))
    #     if abc != None:
    #         config_id = request.env['url.config'].sudo().search([],order="id desc", limit=1)
    #         y = config_id.suffix_category_url

    #         if y:
    #             x = abc.replace(y,'')
    #         else:
    #             x = abc.replace('False','')

    #         category = request.env['product.public.category'].sudo().search([('url_redirect', '=', x)], limit=1)
    #         if not category or not category.can_access_from_current_website():
    #             raise NotFound()
    #     else:
    #         if category:
    #             if isinstance(category, str):
    #                 category = request.env['product.public.category'].search([('id', '=',  int(category))], limit=1)
    #             else:
    #                 category = request.env['product.public.category'].search([('id', '=',  category.id)], limit=1)
    #             if not category or not category.can_access_from_current_website():
    #                 raise NotFound()
    #     Category = request.env['product.public.category']
    #     if category:
    #         category = Category.search([('id', '=', int(category))], limit=1)
    #         if not category or not category.can_access_from_current_website():
    #             raise NotFound()
    #     else:
    #         category = Category

    #     if ppg:
    #         try:
    #             ppg = int(ppg)
    #             post['ppg'] = ppg
    #         except ValueError:
    #             ppg = False
    #     else:
    #         ppg = PPG
    #     if not ppg:
    #         ppg = request.env['website'].get_current_website().shop_ppg or 20

    #     ppr = request.env['website'].get_current_website().shop_ppr or 4

    #     attrib_list = request.httprequest.args.getlist('attrib')
    #     attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
    #     attributes_ids = {v[0] for v in attrib_values}
    #     attrib_set = {v[1] for v in attrib_values}
    #     brand = request.httprequest.args.getlist('brand')
    #     brand_set1 = [[int(x) for x in v] for v in brand if v]
    #     brand_set = [v[0] for v in brand_set1]
    #     filter_list = request.httprequest.args.getlist('filter')
        
    #     filter_values = [[int(x) for x in v.split("-")] for v in filter_list if v]
    #     filter_ids = {v[0] for v in filter_values}
    #     filter_set = {v[1] for v in filter_values}

    #     if brand_set:
    #         brand_record = request.env['product.brand'].search([('id', 'in', brand_set)])
    #     else:
    #         brand_record = False
        
    #     domain = self._get_search_domain(search, category, attrib_values, filter_values, brand_set)

    #     keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))
    #     pricelist_context, pricelist = self._get_pricelist_context()

    #     request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

    #     url = "/shop"
    #     if search:
    #         post["search"] = search
    #         AllBrands = request.env['product.brand'].search([('name','ilike',search)])
    #         ids = []
    #         for i in AllBrands:
    #             ids.append(i.id)
    #         domain_new = [('brand_id', 'in', ids)]
        
    #     if category:
    #         category = request.env['product.public.category'].browse(int(category))
    #         url = "/shop/category/%s" % slug(category)
    #     if attrib_list:
    #         post['attrib'] = attrib_list
        
    #     if brand_set:
    #         post['brand'] = brand_set
    #     if filter_list:
    #         post['filter'] = filter_list

    #     Product = request.env['product.template'].with_context(bin_size=True)
    #     setting = request.env['res.config.settings'].sudo().search([], order=' id desc', limit=1)

    #     list_of_product = []
    #     hide_product = []
    #     hide_product_cat = []
    #     if category:    
    #         parent_category_ids = [category.id]
    #         current_category = category
    #         while current_category.parent_id:
    #             parent_category_ids.append(current_category.parent_id.id)
    #             current_category = current_category.parent_id

    #     if request.env.user.partner_id.hide_product_ids:
    #         for p_id in request.env.user.partner_id.hide_product_ids:
    #             hide_product.append(p_id.id)

    #     if request.env.user.partner_id.hide_product_categ_ids:
    #         for c_id in request.env.user.partner_id.hide_product_categ_ids:
    #             hide_product_categ_ids = request.env['product.template'].sudo().search([('categ_id','=',c_id.id)])
    #             for category_ids in hide_product_categ_ids:
    #                 hide_product_cat.append(category_ids.id)

    #     if request.env.user.partner_id.product_ids:
    #         for p_id in request.env.user.partner_id.product_ids:
    #             if p_id.id not in hide_product:
    #                 list_of_product.append(p_id.id)
        
    #     if request.env.user.partner_id.product_categ_ids:
    #         for c_id in request.env.user.partner_id.product_categ_ids:
    #             product_categ_ids = request.env['product.template'].sudo().search([('categ_id','=',c_id.id)])
    #             for category_ids in product_categ_ids:
    #                 if category_ids.id not in hide_product_cat:
    #                     list_of_product.append(category_ids.id)

    #     if request.env.user.partner_id:
    #         domain+= [('id','in',list_of_product)] 

    #     visitor_product = []
    #     visitor_product_cat = []
    #     if setting.visitor_hide_product_ids:
    #         for p_id in setting.visitor_hide_product_ids:
    #             visitor_product.append(p_id.id)
    #     if setting.visitor_product_categ_ids:
    #         for c_id in setting.visitor_hide_product_categ_ids:
    #             visitor_hide_product_categ_ids = request.env['product.template'].sudo().search([('categ_id','=',c_id.id)])
    #             for category_ids in visitor_hide_product_categ_ids:
    #                 visitor_product_cat.append(category_ids.id)

    #     if setting.visitor_product_ids:
    #         for p_id in setting.visitor_product_ids:
    #             if p_id.id not in visitor_product:
    #                 list_of_product.append(p_id.id)
    #     if setting.visitor_product_categ_ids:
    #         for c_id in setting.visitor_product_categ_ids:
    #             product_categ_ids = request.env['product.template'].sudo().search([('categ_id','=',c_id.id)])
    #             for category_ids in product_categ_ids:
    #                 if category_ids.id not in visitor_product_cat:
    #                     list_of_product.append(category_ids.id)
    #     if setting:
    #         domain+= [('id','in',list_of_product)] 

    #     search_product = Product.search(domain)
    #     search_categories = False
    #     if search:
    #         categories = search_product.mapped('public_categ_ids')
    #         search_categories = Category.search([('id', 'parent_of', categories.ids)] + request.website.website_domain())
    #         categs = search_categories.filtered(lambda c: not c.parent_id)
    #     else:
    #         categs = Category.search([('parent_id', '=', False)] + request.website.website_domain())

    #     website_domain = request.website.website_domain()
    #     categs_domain = [('parent_id', '=', False)] + website_domain
    #     if search:
    #         search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
    #         categs_domain.append(('id', 'in', search_categories.ids))
    #     else:
    #         search_categories = Category
    #     categs = Category.search(categs_domain)

    #     if category:
    #         url = "/shop/category/%s" % slug(category)

    #     config_id = request.env['url.config'].sudo().search([],order="id desc", limit=1)
    #     categ_extension = ''
    #     if config_id:
    #         categ_extension = config_id.suffix_category_url
    #     else:
    #         categ_extension = '.htm'
    #     parent_category_ids = []
    #     if abc != None:
    #         url = "/shop/category/%s%s" % (category.url_redirect,categ_extension)
    #         parent_category_ids = [category.id]
    #         current_category = category
    #         while current_category.parent_id:
    #             parent_category_ids.append(current_category.parent_id.id)
    #             current_category = current_category.parent_id
    #     if abc == None:
    #         if category:
    #             url = "/shop/category/%s" % slug(category)
    #             parent_category_ids = [category.id]
    #             current_category = category
    #             while current_category.parent_id:
    #                 parent_category_ids.append(current_category.parent_id.id)
    #                 current_category = current_category.parent_id

    #     product_count = len(search_product)
    #     pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
    #     products = Product.search(domain, limit=ppg, offset=pager['offset'])

    #     ProductAttribute = request.env['product.attribute']
    #     ProductBrand = request.env['product.brand']
    #     ProductFilter = request.env['product.filter']

    #     if products:
    #         # get all products without limit
    #         attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
    #         brands = ProductBrand.search([])
    #     else:
    #         attributes = ProductAttribute.browse(attributes_ids)
    #         brands = ProductBrand.browse(brand_set)
    #     filters = grouped_tasks = None
    #     if products:
    #         # get all products without limit
    #         selected_products = Product.search(domain, limit=False)
            
    #         filters = ProductFilter.search([('filter_value_ids', '!=', False), ('filter_ids.product_tmpl_id', 'in', selected_products.ids)])
            
    #     else:
    #         filters = ProductFilter.browse(filter_ids)

    #     filter_group = request.env['group.filter'].search([])
        
    #     applied_filter = False
    #     if filter_values:
    #         applied_filter = True

    #     if filter_group:
    #         grouped_tasks = [request.env['product.filter'].concat(*g) for k, g in groupbyelem(filters, itemgetter('group_id'))]
    #     else:
    #         grouped_tasks = [filters]

    #     prods  = Product.sudo().search(domain)
    #     request.website.sudo().get_dynamic_count(prods)

    #     layout_mode = request.session.get('website_sale_shop_layout_mode')
    #     if not layout_mode:
    #         if request.website.viewref('website_sale.products_list_view').active:
    #             layout_mode = 'list'
    #         else:
    #             layout_mode = 'grid'

    #     compute_currency = self._get_compute_currency(pricelist, products[:1])

    #     keep = QueryURL('/shop', category=category and int(category), search=search,brand=brand_set, attrib=attrib_list, order=post.get('order'))

    #     values = {
    #         'search': search,
    #         'category': category,
    #         'attrib_values': attrib_values,
    #         'attrib_set': attrib_set,
    #         'brand_set': brand_set,
    #         'brand_record': brand_record,
    #         'filter_set': filter_set,
    #         'filter_values': filter_values,
    #         'pager': pager,
    #         'pricelist': pricelist,
    #         'grouped_tasks':grouped_tasks,
    #         'add_qty': add_qty,
    #         'products': products,
    #         'search_count': product_count,  # common for all searchbox
    #         'bins': TableCompute().process(products, ppg),
    #         'rows': PPR,
    #         'ppg': ppg,
    #         'ppr': ppr,
    #         'categories': categs,
    #         'filters': filters,
    #         'attributes': attributes,
    #         'keep': keep,
    #         'brands':brands,
    #         'parent_category_ids': parent_category_ids,
    #         'search_categories_ids': search_categories.ids,
    #         'layout_mode': layout_mode,
    #         'seo_url' : dict(zip([p.id for p in products], [p.url_redirect for p in products ])),
    #         'config_id' : config_id
    #     }

        
    #     if 'seo_url' in values:
    #         for j,k in values['seo_url'].items():
    #             if k == False or k == '':
    #                 pro = Product.sudo().search([('id','=',int(j))],limit=1)
    #                 values['seo_url'].update({j : slug(pro)})

    #     if category:
    #         values['main_object'] = category
    #     return request.render("website_sale.products", values)

    @http.route(['''/shop/product/<model("product.template"):product>''',
        '''/shop/product/<abc>'''], type='http', auth="public", website=True)
    def product(self, product=None, abc=None, category = '', search = '',  **kwargs):
        if product == None:
            if abc != None:
                config_id = request.env['url.config'].sudo().search([],order="id desc", limit=1)
                if config_id:
                    y = config_id.suffix_product_url
                    if y:
                        x = abc.replace(y,'')
                    else:
                        x = abc.replace('False','')

                    product = request.env['product.template'].sudo().search([('url_redirect','=',x)],limit=1)
                    if not product:
                        z = unslug_url(x)
                        if z and isinstance(z, int):
                            product = request.env['product.template'].sudo().search([('id','=',int(z))],limit=1)
                            if not product:
                                raise NotFound()
                        else:
                            raise NotFound()
                else:
                    z = unslug_url(abc)
                    if z and isinstance(z, int):
                        product = request.env['product.template'].sudo().search([('id','=',int(z))],limit=1)
                        if not product:
                            raise NotFound()
                    else:
                        raise NotFound()
            else:
                raise NotFound()
        else:
            if not product.can_access_from_current_website():
                raise NotFound()

        add_qty = int(kwargs.get('add_qty', 1))

        product_context = dict(request.env.context, quantity=add_qty,
                               active_id=product.id,
                               partner=request.env.user.partner_id)
        ProductCategory = request.env['product.public.category']

        if category:
            category = ProductCategory.browse(int(category)).exists()

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attrib_set = {v[1] for v in attrib_values}

        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)

        categs = ProductCategory.search([('parent_id', '=', False)])

        pricelist = request.website.get_current_pricelist()

        attachment_obj = request.env['product.attachment']
        attachments = attachment_obj.sudo().search([('product_tmpl_id', '=', product.id)])

        
        def compute_currency(price):
            return product.currency_id._convert(price, pricelist.currency_id, product._get_current_company(pricelist=pricelist, website=request.website), fields.Date.today())

        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)
        values = {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categs,
            'main_object': product,
            'product': product,
            'add_qty': add_qty,
            'attachments': attachments,
            'optional_product_ids': [p.with_context({'active_id': p.id}) for p in product.valid_product_template_attribute_line_ids],
            'seo_url' : 'abcd',
        }
        return request.render("website_sale.product", values)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
