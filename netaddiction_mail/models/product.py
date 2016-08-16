# -*- coding: utf-8 -*-
from datetime import date, timedelta

from openerp import api, models


class Products(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.constrains('sale_ok')
    def _check_sale_ok(self):
        users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
        if self.sale_ok:
            obj = "[SHOPPING] PRODOTTO NON PIU ESAURITO %s id: %s" % (self.name, self.id)
        else:
            obj = "[SHOPPING] PRODOTTO ESAURITO %s id: %s" % (self.name, self.id)
        self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "prodotti", set(users))

    @api.one
    @api.constrains('visible')
    def _check_visible(self):
        users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
        if self.visible:
            obj = "[SHOPPING] PRODOTTO ACCESO %s id: %s" % (self.name, self.id)
        else:
            obj = "[SHOPPING] PRODOTTO SPENTO %s id: %s" % (self.name, self.id)
        self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "prodotti", set(users))

    @api.model
    def _verify_release_date(self):
        users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
        products_out = self.env["product.product"].search([("out_date", "=", date.today() + timedelta(days=7))])
        products_available = self.env["product.product"].search([("available_date", "=", date.today() + timedelta(days=7))])
        for product in products_out:
            obj = "[SHOPPING] PRODOTTO IN USCITA %s id: %s data uscita %s" % (product.name, product.id, product.out_date)
            self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "prodotti", set(users))
        for product in products_available:
            obj = "[SHOPPING] PRODOTTO DISPONIBILE IN 7 GIORNI %s id: %s data uscita %s" % (product.name, product.id, product.available_date)
            self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "prodotti", set(users))
