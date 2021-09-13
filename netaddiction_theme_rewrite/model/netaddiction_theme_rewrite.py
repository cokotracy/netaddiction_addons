# Copyright 2021 Netaddiction

# Documentation links
# https://www.odoo.com/documentation/12.0/reference/http.html

from datetime import date, timedelta
from odoo.http import request, route, Controller
from odoo import models, fields
from odoo.addons.odoo_website_wallet.controllers.main import WebsiteWallet as Wallet
from odoo.addons.website_sale.controllers.main import WebsiteSale as Shop
import locale

locale.setlocale(locale.LC_ALL, 'it_IT.utf8')

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


#SOSTITUISCE LA HOME
class CustomHome(Controller):
    @route('/', type='http', auth='public', website=True)
    def controller(self, **post):
        preorder_list = request.env["product.template"].sudo().search([('out_date', '>', date.today().strftime("%Y-%m-%d"))], limit=20)
        return request.render("netaddiction_theme_rewrite.template_home_secondary", {'preorder_list':preorder_list})

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

    
   