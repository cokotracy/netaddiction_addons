# Copyright 2021 Netaddiction

# Documentation links
# https://www.odoo.com/documentation/12.0/reference/http.html

from odoo import http
from odoo.http import request, route, Controller
from odoo import models, fields
from odoo.addons.odoo_website_wallet.controllers.main import WebsiteWallet as Wallet

#SOSTITUISCE LA HOME
class CustomHome(Controller):
    @route('/', type='http', auth='public', website=True)
    def controller(self, **post):
        return request.render("netaddiction_theme_rewrite.template_home_secondary", {})

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


#AGGIUNGE ALLA FORM DELLE CATEGORIE IL CAMPO DI INSERIMENTO DESCRIZIONE
class CategoryDescriptionInherit(models.Model):
    _inherit = 'product.public.category'
    description = fields.Text(name='description')
    
#AGGIUNGE LA PAGINA COSTI DI SPEDIZIONECREA DELLE PAGINE DINAMICHE PER I TAG
class CustomTagPage(http.Controller):
    @http.route(['/tag/<string:tag_name>'], type='http',auth='public',website=True) 
    def controller(self, tag_name, **kw):

        tag = request.env['product.template.tag'].sudo().search([('name', '=', tag_name)])

        if not tag.id:
            page = request.website.is_publisher() and 'website.page_404' or 'http_routing.404'
            return request.render(page, {})

        page_size = 15
        start_element  = 0
        current_page = 0

        if(kw.get('page')):
            current_page = (int(kw.get('page')) - 1)
            start_element = (page_size * (int(kw.get('page')) - 1))

        
        full_product_id = request.env["product.template"].sudo().search([('tag_ids', '=', tag.id)])
        product_count = len(full_product_id)

        if((start_element + page_size) > (product_count - 1)):
            product_list_id = full_product_id[start_element:product_count]
        else:
            if(start_element > 0):
                product_list_id = full_product_id[(start_element - 1):page_size]
            else:
                product_list_id = full_product_id[start_element:page_size]

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
        return request.render("netaddiction_theme_rewrite.wallet_balance",{'wallet':price})


