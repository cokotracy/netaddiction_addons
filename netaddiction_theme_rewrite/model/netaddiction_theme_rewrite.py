# Copyright 2021 Netaddiction

# Documentation links
# https://www.odoo.com/documentation/12.0/reference/http.html

from odoo import http
from odoo.http import request, route, Controller
from odoo import models, fields

#SOSTITUISCE LA HOME
class CustomHome(Controller):
    @route('/', type='http', auth='public', website=True)
    def controller(self, **post):
        return request.render("netaddiction_theme_rewrite.template_home_secondary", {})


class CustomPrivacy(Controller):
    @route('/privacy/', type='http', auth='public', website=True)
    def controller(self, **post):
        return request.render("netaddiction_theme_rewrite.template_privacy_policy", {})


class CustomShipping(Controller):
    @route('/costi-metodi-spedizione/', type='http', auth='public', website=True)
    def controller(self, **post):
        return request.render("netaddiction_theme_rewrite.template_shipping_terms", {})


#AGGIUNGE ALLA FORM DELLE CATEGORIE IL CAMPO DI INSERIMENTO DESCRIZIONE
class CategoryDescriptionInherit(models.Model):
    _inherit = 'product.public.category'
    description = fields.Text(name='description')
    

class CustomTagPage(http.Controller):
    @http.route(['/tag/<string:tag_name>'], type='http',auth='public',website=True) 
    def controller(self, tag_name, **kw):

        try:
            query = f"SELECT id FROM product_template_tag WHERE name ='{tag_name}'"
        except IndexError:
            query = ""

        request.env.cr.execute(query)
        tag_id = request.env.cr.dictfetchall()

        if (len(tag_id) < 1):
            page = request.website.is_publisher() and 'website.page_404' or 'http_routing.404'
            return request.render(page, {})


        page_size = 15
        start_element  = 0
        current_page = 0

        if(kw.get('page')):
            current_page = (int(kw.get('page')) - 1)
            start_element = (page_size * (int(kw.get('page')) - 1))

        try:
            query = f"SELECT product_tmpl_id as id FROM product_template_product_tag_rel WHERE tag_id = '{tag_id[0]['id']}' ORDER BY id DESC"
        except IndexError:
            query = ""

        request.env.cr.execute(query)
        full_product_id = request.env.cr.dictfetchall()
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




