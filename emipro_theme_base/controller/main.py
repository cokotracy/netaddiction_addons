# -*- coding: utf-8 -*-
"""
    This file is used for create and inherit the core controllers
"""
import datetime
import json
from datetime import timedelta, date
from odoo.http import request, Controller, route
from odoo.tools.safe_eval import safe_eval
from werkzeug.exceptions import NotFound
import werkzeug
from odoo import fields, models, http

from odoo import http
import odoo
import logging
from odoo.tools.translate import _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import Website
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.sale.controllers.variant import VariantController
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist

_logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):

    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        """
        category wise product search and blog, category and product search
        :return: res
        """
        if 'cat_id' in options.keys():
            options['category'] = options.get('cat_id')
        res = super(WebsiteSale, self).products_autocomplete(term, options=options, **kwargs)
        res['blogs_count'] = 0
        categories = blogs = []

        if 'search_in' in options.keys() and request.website.is_advanced_search:
            limit = options.get('limit', 5)
            if not options.get('search_in') or options.get('search_in') == 'all':
                categories = self.get_searched_category(term,
                                                        limit) if request.website.allowed_search_category else False
                blogs = self.get_searched_blog(term, limit) if request.website.allowed_search_blog else False
                blogs_count = request.env['blog.post'].sudo().search_count(
                    [('name', 'ilike', term), ('website_id', 'in', [False, request.website.id])])
                res['blogs_count'] = blogs_count
            elif options.get('search_in') == 'category':
                categories = self.get_searched_category(term, limit)
                res['products'] = {}
            elif options.get('search_in') == 'blog':
                blogs = self.get_searched_blog(term, limit)
                blogs_count = request.env['blog.post'].sudo().search_count(
                    [('name', 'ilike', term), ('website_id', 'in', [False, request.website.id]),
                     ('website_published', '=', True)])
                res['products'] = {}
                res['blogs_count'] = blogs_count
        res['categories'] = categories.read(['id', 'name']) if categories else False
        res['blogs'] = blogs.read(['id', 'blog_id', 'name']) if blogs else False
        return res

    def get_searched_category(self, term, limit):
        return request.env['product.public.category'].sudo().search(
            [('name', 'ilike', term), ('website_id', 'in', [False, request.website.id])], limit=limit)

    def get_searched_blog(self, term, limit):
        return request.env['blog.post'].sudo().search([('name', 'ilike', term), ('website_published', '=', True),
                                                       ('website_id', 'in', [False, request.website.id])], limit=limit)


class EmiproThemeBase(http.Controller):

    @http.route(['/get_banner_video_data'], type='json', auth="public", website=True)
    def get_banner_video_data(self, is_ios):
        template = request.env['ir.ui.view'].sudo().search([('key', '=', 'theme_clarico_vega.banner_video_template')])
        if template:
            values = {
                'banner_video_url': request.website.banner_video_url or False,
                'is_ios': is_ios,
            }
            response = http.Response(template="theme_clarico_vega.banner_video_template", qcontext=values)
            return response.render()

    @http.route(['/mega_menu_content_dynamic'], type='json', auth="public", website=True)
    def mega_menu_content_dynamic(self, menu_id):
        response = http.Response(template="emipro_theme_base.website_dynamic_category")
        current_menu = request.env['website.menu'].sudo().search([('id', '=', menu_id)])
        if current_menu.is_dynamic_menu and current_menu.mega_menu_content_dynamic != response.render().decode():
            current_menu.write({"mega_menu_content_dynamic": response.render().decode(), "is_dynamic_menu_json": False})
            return response.render().decode()
        else:
            return False

    @http.route(['/dynamic_mega_menu_child'], type='json', auth="public", website=True)
    def dynamic_mega_menu_child(self, category_id):
        current_category = request.env['product.public.category'].sudo().search([('id', '=', category_id)])
        if current_category:
            values = {
                'child_ids': current_category.child_id,
            }
            response = http.Response(template="emipro_theme_base.dynamic_mega_menu_child", qcontext=values)
            return response.render()

    @http.route(['/quick_view_item_data'], type='json', auth="public", website=True)
    def get_quick_view_item(self, product_id=None):
        """
        This controller return the template for QuickView with product details
        :param product_id: get product id
        :return: quick_view template html
        """
        if product_id:
            product = request.env['product.template'].search([['id', '=', product_id]])
            values = {
                'product': product,
            }
            response = http.Response(template="emipro_theme_base.quick_view_container", qcontext=values)
            return response.render()

    @http.route(['/shop/cart/update_custom'], type='json', auth="public", methods=['GET', 'POST'], website=True,
                csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, product_custom_attribute_values=None, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        # product_custom_attribute_values = None
        if product_custom_attribute_values:
            product_custom_attribute_values = json.loads(product_custom_attribute_values)

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        if sale_order:
            sale_order._cart_update(
                product_id=int(product_id),
                add_qty=add_qty,
                set_qty=set_qty,
                product_custom_attribute_values=product_custom_attribute_values,
                no_variant_attribute_values=no_variant_attribute_values,
                )
            return True
        else:
            return False

    @http.route(['/ajax_cart_item_data'], type='json', auth="public", website=True)
    def get_ajax_cart_item(self, product_id=None):
        """
        This controller return the template for Ajax Add to Cart with product details
        :param product_id: get product id
        :return: ajax cart template for variants html
        """
        if product_id:
            product = request.env['product.template'].search([['id', '=', product_id]])
            values = {
                'product': product,
            }
            response = http.Response(template="emipro_theme_base.ajax_cart_container", qcontext=values)
            return response.render()

    @http.route(['/ajax_cart_sucess_data'], type='json', auth="public", website=True)
    def get_ajax_cart_sucess(self, product_id=None, product_product=None):
        """
        This controller return the template for Ajax Add to Cart with product details
        :param product_id: get product id
        :return: ajax cart template for success html
        """
        if product_id:
            product = request.env['product.template'].search([['id', '=', product_id]])
            product_variant = request.env['product.product'].search([['id', '=', product_product]])
            values = {
                'product': product,
                'product_variant': product_variant,
            }
            response = http.Response(template="emipro_theme_base.ajax_cart_success_container", qcontext=values)
            return response.render()

    @http.route([
        '/brand-listing',
    ], type='http', auth="public", website=True)
    def brand_listing(self):
        return request.render('theme_clarico_vega.brand_listing_template')


class EmiproThemeBaseExtended(WebsiteSaleWishlist):

    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        """
        Inherit method for implement Price Filter and Brand Filter
        :param search:
        :param category:
        :param attrib_values:
        :return: search domain
        """

        domain = super(EmiproThemeBaseExtended, self)._get_search_domain(search=search, category=category,
                                                                         attrib_values=attrib_values,
                                                                         search_in_description=True)
        cust_min_val = request.httprequest.values.get('min_price', False)
        cust_max_val = request.httprequest.values.get('max_price', False)

        if cust_max_val and cust_min_val:
            try:
                cust_max_val = float(cust_max_val)
                cust_min_val = float(cust_min_val)
            except ValueError:
                raise NotFound()
            products = request.env['product.template'].sudo().search(domain)
            new_prod_ids = []
            pricelist = request.website.pricelist_id
            # return the product ids as per option selected (sale price or discounted price)
            if products:
                if request.website.price_filter_on == 'website_price':
                    context = dict(request.context, quantity=1, pricelist=pricelist.id if pricelist else False)
                    products = products.with_context(context)
                    new_prod_ids = products.filtered(
                        lambda r: r.price >= float(cust_min_val) and r.price <= float(cust_max_val)).ids
                else:
                    new_prod_ids = products.filtered(
                        lambda r: r.currency_id._convert(r.lst_price, pricelist.currency_id,
                                                         request.website.company_id, date=fields.Date.today()) >= float(
                            cust_min_val) and
                                  r.currency_id._convert(r.lst_price, pricelist.currency_id,
                                                         request.website.company_id, date=fields.Date.today()) <= float(
                            cust_max_val)).ids
                domain += [('id', 'in', new_prod_ids)]
            else:
                domain = [('id', '=', False)]
        if attrib_values:
            ids = []
            # brand Filter
            for value in attrib_values:
                if value[0] == 0:
                    ids.append(value[1])
                    domain += [('product_brand_ept_id.id', 'in', ids)]
        return domain


class EptWebsiteSaleVariantController(VariantController):

    @http.route(['/sale/get_combination_info_website'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        """
        Inherit this method because set the product offer timer data if it's available
        :return: result
        """

        res = super(EptWebsiteSaleVariantController, self).get_combination_info_website(
            product_template_id=product_template_id,
            product_id=product_id,
            combination=combination,
            add_qty=add_qty, **kw)
        product = request.env['product.product'].sudo().search([('id', '=', res.get('product_id'))])
        partner = request.env['res.users'].sudo().search([('id', '=', request.uid)]).partner_id
        products_qty_partner = []
        products_qty_partner.append((product, add_qty, partner))
        pricelist = request.website.get_current_pricelist()
        suitable_rule = False
        res.update({'is_offer': False})
        # set internal reference
        product_temp = request.env['product.template'].sudo().search([('id', '=', product_template_id)])
        res.update({
                       'sku_details': product.default_code if product_temp.product_variant_count > 1 else product_temp.default_code})
        try:
            if pricelist and product:
                vals = pricelist._compute_price_rule(products_qty_partner)
                if vals.get(int(product)) and vals.get(int(product))[1]:
                    suitable_rule = vals.get(int(product))[1]
                    suitable_rule = request.env['product.pricelist.item'].sudo().search(
                        [('id', '=', suitable_rule), ('is_display_timer', '=', True)])
                    if suitable_rule.date_end and (
                            suitable_rule.applied_on == '3_global' or suitable_rule.product_id or suitable_rule.product_tmpl_id or suitable_rule.categ_id):
                        start_date = int(round(datetime.datetime.timestamp(suitable_rule.date_start) * 1000))
                        end_date = int(round(datetime.datetime.timestamp(suitable_rule.date_end) * 1000))
                        current_date = int(round(datetime.datetime.timestamp(datetime.datetime.now()) * 1000))
                        res.update({'is_offer': True,
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'current_date': current_date,
                                    'suitable_rule': suitable_rule,
                                    'offer_msg': suitable_rule.offer_msg,
                                    })
        except Exception as e:
            return res
        return res


class Website(Website):

    @http.route(website=True, auth="public", sitemap=False, csrf=False)
    def web_login(self, *args, **kw):
        """
            Login - overwrite of the web login so that regular users are redirected to the backend
            while portal users are redirected to the same page from popup
            Returns formatted data required by login popup in a JSON compatible format
        """
        login_form_ept = kw.get('login_form_ept', False)
        if kw.get('login_form_ept', False):
            kw.pop('login_form_ept')
        response = super(Website, self).web_login(*args, **kw)
        if login_form_ept:
            if response.is_qweb and response.qcontext.get('error', False):
                return json.dumps(
                    {'error': response.qcontext.get('error', False), 'login_success': False, 'hide_msg': False})
            else:
                if request.params.get('login_success', False):
                    uid = request.session.authenticate(request.session.db, request.params['login'],
                                                       request.params['password'])
                    user = request.env['res.users'].browse(uid)
                    redirect = '1'
                    if user.totp_enabled:
                        redirect = request.env(user=uid)['res.users'].browse(uid)._mfa_url()
                        return json.dumps({'redirect': redirect, 'login_success': True, 'hide_msg': True})
                    if user.has_group('base.group_user'):
                        redirect = b'/web?' + request.httprequest.query_string
                        redirect = redirect.decode('utf-8')
                    return json.dumps({'redirect': redirect, 'login_success': True, 'hide_msg': False})
        return response


class AuthSignupHome(Home):

    @http.route(website=True, auth="public", sitemap=False, csrf=False)
    def web_auth_signup(self, *args, **kw):
        """
            Signup from popup and redirect to the same page
            Returns formatted data required by login popup in a JSON compatible format
        """
        signup_form_ept = kw.get('signup_form_ept', False)
        if kw.get('signup_form_ept', False):
            kw.pop('signup_form_ept')
        response = super(AuthSignupHome, self).web_auth_signup(*args, **kw)
        if signup_form_ept:
            if response.is_qweb and response.qcontext.get('error', False):
                return json.dumps({'error': response.qcontext.get('error', False), 'login_success': False})
            else:
                if request.params.get('login_success', False):
                    redirect = '1'
                    return json.dumps({'redirect': redirect, 'login_success': True})
        return response

    @http.route(auth='public', website=True, sitemap=False, csrf=False)
    def web_auth_reset_password(self, *args, **kw):
        """
            Reset password from popup and redirect to the same page
            Returns formatted data required by login popup in a JSON compatible format
        """
        reset_form_ept = kw.get('reset_form_ept', False)
        if kw.get('reset_form_ept', False):
            kw.pop('reset_form_ept')
        response = super(AuthSignupHome, self).web_auth_reset_password(*args, **kw)
        if reset_form_ept:
            if response.is_qweb and response.qcontext.get('error', False):
                return json.dumps({'error': response.qcontext.get('error', False)})
            elif response.is_qweb and response.qcontext.get('message', False):
                return json.dumps({'message': response.qcontext.get('message', False)})
        return response
