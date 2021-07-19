# Copyright 2021 Netaddiction

# Documentation links
# https://www.odoo.com/documentation/12.0/reference/http.html

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
