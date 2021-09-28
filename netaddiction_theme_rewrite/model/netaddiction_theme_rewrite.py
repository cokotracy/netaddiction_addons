# Copyright 2021 Netaddiction

# Documentation links
# https://www.odoo.com/documentation/12.0/reference/http.html

from werkzeug.exceptions import Forbidden, NotFound
from datetime import date, timedelta
from odoo.http import request, route, Controller
from odoo import models, fields, tools
from odoo.addons.odoo_website_wallet.controllers.main import WebsiteWallet as Wallet
from odoo.addons.website_sale.controllers.main import WebsiteSale as Shop
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website

class WebsiteCustom(Website):
    @route(['/shop/cart/check_limit_order'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self):
        order = request.website.sale_get_order(force_create=1)
        for order_line in order.order_line:
            prod = order_line.product_id
            if prod.id > 9:
                if prod.qty_single_order > 0:
                    if order_line.product_qty > prod.qty_single_order:
                        return {'order_limit':prod.qty_single_order, 'product_name':prod.name,'qty_available_now':prod.qty_available_now, "qty_sum_suppliers":prod.qty_sum_suppliers, "out_date":prod.out_date, "sale_ok":prod.sale_ok}

                if prod.qty_limit > 0:
                    orders = request.env['sale.order.line'].search([('product_id', '=', prod.id)])
                    sold = 0
                    for order in orders:
                        sold = sold + order.product_qty
                    
                    if (sold + order_line.product_qty) >= prod.qty_limit:
                        return {'order_limit_total':prod.qty_limit, 'product_name':prod.name,'qty_available_now':prod.qty_available_now, "qty_sum_suppliers":prod.qty_sum_suppliers, "out_date":prod.out_date, "sale_ok":prod.sale_ok}
                
                if(prod.sale_ok == False or prod.qty_sum_suppliers <= 0 and prod.qty_available_now <= 0):
                    if(not prod.out_date or prod.out_date < date.today() or prod.sale_ok == False):     
                        return {'out_of_stock':True, 'product_name':prod.name}
    
    
    @route(['/get_product_from_id'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def get_product_from_id(self, product_id=None):
        prod = request.env['product.product'].search([('id', '=', product_id)])

        return {"qty_sum_suppliers": prod.qty_sum_suppliers, "sale_ok":prod.sale_ok, "qty_available_now":prod.qty_available_now, "out_date":prod.out_date}
        

    
class SiteCategories(Shop):
    @route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True, sitemap=Shop.sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        sup = super(SiteCategories, self).shop(page=page, category=category, search=search, **post)
        Category = request.env['product.public.category']
        if category:
            category = Category.sudo().search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if category:
            preorder_list = request.env["product.template"].sudo().search([
                ('out_date', '>', date.today().strftime("%Y-%m-%d")),
                ('public_categ_ids', 'in', category.id)], limit=20)

            newest_list = request.env["product.template"].sudo().search([
                ('create_date', '>=', (date.today() - timedelta(days = 20)).strftime("%Y-%m-%d")),
                ('create_date', '<=', date.today().strftime("%Y-%m-%d")),
                ('public_categ_ids', 'in', category.id),
                '|',
                ('out_date', '<=', date.today().strftime("%Y-%m-%d")), ('out_date', '=', False)
                ], limit=20)

            bestseller_list_temp = request.env['sale.order.line'].sudo().read_group(
                domain=[
                    ('create_date', '>=', (date.today() - timedelta(days = 20)).strftime("%Y-%m-%d")),
                    ('create_date', '<=', date.today().strftime("%Y-%m-%d")),
                    ('qty_invoiced', '>', 0),
                    ('product_id', '>', 9),
                    ('product_id.product_tmpl_id.public_categ_ids', 'in', category.id)
                ], fields=['product_id'], groupby=['product_id'], limit=20, orderby="qty_invoiced desc"
            )
            
            bestseller_list = []

            for prod in bestseller_list_temp:
                bestseller_list.append(request.env['product.product'].sudo().search([('id', '=', prod['product_id'][0])]).product_tmpl_id)

        
            sup.qcontext["category"] = category
            sup.qcontext["preorder_list"] = preorder_list
            sup.qcontext["newest_list"] = newest_list
            sup.qcontext["bestseller_list"] = bestseller_list
            
        return sup


#AGGIUNGE LA PAGINA PRIVACY
class CustomPrivacy(Controller):
    @route('/privacy/', type='http', auth='public', website=True)
    def controller(self, **post):
        return request.render("netaddiction_theme_rewrite.template_privacy_policy", {})

#AGGIUNGE LA PAGINA COSTI DI SPEDIZIONE
class CustomShipping(Controller):
    @route('/costi-metodi-spedizione/', type='http', auth='public', website=True)
    def controller(self, **post):
        return request.render("netaddiction_theme_rewrite.template_shipping_terms", {})


#AGGIUNGE PAGINE DINAMICHE PER I TAG
class CustomTagPage(Controller):
    @route(['/tag/<string:tag_name>'], type='http',auth='public',website=True) 
    def controller(self, tag_name, **kw):

        tag = request.env['product.template.tag'].sudo().search([('name', '=', tag_name)])

        if not tag.id:
            page = request.website.is_publisher() and 'website.page_404' or 'http_routing.404'
            return request.render(page, {})

        page_size = 15
        start_element = 0
        current_page = 0

        if(kw.get('page')):
            current_page = (int(kw.get('page')) - 1)
            start_element = (page_size * (int(kw.get('page')) - 1))

        product_count = request.env["product.template"].sudo().search_count([('tag_ids', '=', tag.id)])
        product_list_id = request.env["product.template"].sudo().search([('tag_ids', '=', tag.id)], limit=page_size, offset=start_element)
        page_number = (product_count / page_size)

        if(page_number > int(page_number)):
            page_number = (page_number + 1)
        
        values = {
            'tag_name': tag_name,
            'page_number':int(page_number),
            'current_page':current_page,
            'page_size':page_size,
            'product_list_id':product_list_id
        }
        return request.render("netaddiction_theme_rewrite.template_tag", values)


#ESTENDE LA WALLET BALANCE PAGE
class WalletPageOverride(Wallet):
    @route(
        ['/wallet']
        , type='http', auth='public', website=True)
    def wallet_balance(self, **post):
        sup = super(WalletPageOverride, self).wallet_balance()
        return request.render("netaddiction_theme_rewrite.wallet_balance", sup.qcontext)

    @route(
        ['/add/wallet/balance']
        , type='http', auth='public', website=True)
    def add_wallet_balance(self, **post):
        sup = super(WalletPageOverride, self).add_wallet_balance()
        return request.render("netaddiction_theme_rewrite.add_wallet_balance", sup.qcontext)


#CUSTOM ADDRESS TEMPLATE
class WebsiteSaleCustomAddress(Controller):
    @route(['/shop/address-edit'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ('new', 'shipping')
                        partner_id = -1
                    elif partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            partner_fields = request.env['res.partner']._fields
            pre_values = {
                k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == 'many2one' else v
                for k, v in kw.items()
            }
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect('/my/home')

        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'error': errors,
            'callback': kw.get('callback'),
            'only_services': order and order.only_services,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("netaddiction_theme_rewrite.address_custom", render_values)

    def checkout_form_validate(self, mode, all_form_values, data):
        # mode: tuple ('new|edit', 'billing|shipping')
        # all_form_values: all values before preprocess
        # data: values after preprocess
        error = dict()
        error_message = []

        # Required fields from form
        required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]

        # Required fields from mandatory field function
        country_id = int(data.get('country_id', False))
        required_fields += mode[1] == 'shipping' and self._get_mandatory_fields_shipping(country_id) or self._get_mandatory_fields_billing(country_id)

        # error message for empty required fields
        for field_name in required_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append('Invalid Email! Please enter a valid email address.')

        # vat validation
        Partner = request.env['res.partner']
        if data.get("vat") and hasattr(Partner, "check_vat"):
            if country_id:
                data["vat"] = Partner.fix_eu_vat_number(country_id, data.get("vat"))
            partner_dummy = Partner.new(self._get_vat_validation_fields(data))
            try:
                partner_dummy.check_vat()
            except ValidationError as exception:
                error["vat"] = 'error'
                error_message.append(exception.args[0])

        if [err for err in error.values() if err == 'missing']:
            error_message.append('Some required fields are empty.')

        return error, error_message

    def _get_mandatory_fields_billing(self, country_id=False):
        req = self._get_mandatory_billing_fields()
        if country_id:
            country = request.env['res.country'].browse(country_id)
            if country.state_required:
                req += ['state_id']
            if country.zip_required:
                req += ['zip']
        return req

    def _get_mandatory_fields_shipping(self, country_id=False):
        req = self._get_mandatory_shipping_fields()
        if country_id:
            country = request.env['res.country'].browse(country_id)
            if country.state_required:
                req += ['state_id']
            if country.zip_required:
                req += ['zip']
        return req

    def _get_mandatory_billing_fields(self):
        # deprecated for _get_mandatory_fields_billing which handle zip/state required
        return ["name", "email", "street", "city", "country_id"]

    def _get_mandatory_shipping_fields(self):
        # deprecated for _get_mandatory_fields_shipping which handle zip/state required
        return ["name", "street", "city", "country_id"]

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
                    return Forbidden()
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values = {}
        authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()
        for k, v in values.items():
            # don't drop empty value, it could be a field to reset
            if k in authorized_fields and v is not None:
                new_values[k] = v
            else:  # DEBUG ONLY
                if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
                    _logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)

        new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
        new_values['user_id'] = request.website.salesperson_id and request.website.salesperson_id.id

        if request.website.specific_user_account:
            new_values['website_id'] = request.website.id

        if mode[0] == 'new':
            new_values['company_id'] = request.website.company_id.id

        lang = request.lang.code if request.lang.code in request.website.mapped('language_ids.code') else None
        if lang:
            new_values['lang'] = lang
        if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
            new_values['type'] = 'other'
        if mode[1] == 'shipping':
            new_values['parent_id'] = order.partner_id.commercial_partner_id.id
            new_values['type'] = 'delivery'

        return new_values, errors, error_msg


    def _get_country_related_render_values(self, kw, render_values):
        '''
        This method provides fields related to the country to render the website sale form
        '''
        values = render_values['checkout']
        mode = render_values['mode']
        order = render_values['website_sale_order']

        def_country_id = order.partner_id.country_id
        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or def_country_id

        res = {
            'country': country,
            'country_states': country.get_website_sale_states(mode=mode[1]),
            'countries': country.get_website_sale_countries(mode=mode[1]),
        }
        return res