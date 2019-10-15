# -*- coding: utf-8 -*-

from openerp import api, models


class OfferCatalogLine(models.Model):
    _inherit = "netaddiction.specialoffer.offer_catalog_line"

    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active and self.offer_catalog_id.active and self.qty_limit > 0 and self.qty_selled >= self.qty_limit:
            # TODO risistemare acl per mail o fare menu di configurazione
            # users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
            # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
            # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_offers")
            users_2 = "andrea.alunni@netaddiction.it, riccardo.ioni@netaddiction.it"
            obj = "[SHOPPING] OFFERTA CATALOGO %s spenta  per il prodotto %s" % (self.offer_catalog_id.name, self.product_id.name)
            # self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "shopping@multiplayer.com", set(users))
            self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients(obj, obj, "shopping@multiplayer.com", users_2)


class OfferCartLine(models.Model):
    _inherit = "netaddiction.specialoffer.offer_cart_line"

    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active and self.offer_cart_id.active and self.qty_limit > 0 and self.qty_selled >= self.qty_limit:
            # TODO risistemare acl per mail o fare menu di configurazione
            # users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
            # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
            # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_offers")
            users_2 = "andrea.alunni@netaddiction.it, riccardo.ioni@netaddiction.it"
            obj = "[SHOPPING] OFFERTA CARRELLO %s spenta  per il prodotto %s" % (self.offer_cart_id.name, self.product_id.name)
            # self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "shopping@multiplayer.com", set(users))
            self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients(obj, obj, "shopping@multiplayer.com", users_2)
