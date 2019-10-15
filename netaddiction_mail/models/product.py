# -*- coding: utf-8 -*-
from datetime import date, timedelta

from openerp import api, models


class Products(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.constrains('sale_ok')
    def _check_sale_ok(self):
        if self.env.context.get('skip_notification_mail', False):
            return

        if not self.sale_ok:
            included_categories = []
            included_categories.append(self.env["product.category"].search([("name", "=", "Videogiochi")]).id)
            included_categories.append(self.env["product.category"].search([("name", "=", "Gadget")]).id)
            included_categories.append(self.env["product.category"].search([("name", "=", "Figures")]).id)
            included_categories.append(self.env["product.category"].search([("name", "=", "Modellismo e Model Kit")]).id)

        # TODO risistemare acl per mail o fare menu di configurazione
        # users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
            if self.categ_id.id in included_categories:
                obj = "[SHOPPING] PRODOTTO ESAURITO [%s] %s id: %s" % (self.categ_id.name, self.name, self.id)
                users_2 = "andrea.alunni@netaddiction.it, riccardo.ioni@netaddiction.it"
            # self.env["netaddiction.email.dispatcher"].send_notification(obj, obj, "shopping@multiplayer.com", set(users))
                self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients(obj, obj, "shopping@multiplayer.com", users_2)

    @api.one
    @api.constrains('visible')
    def _check_visible(self):
        if self.env.context.get('skip_notification_mail', False):
            return
        # TODO risistemare acl per mail o fare menu di configurazione
        # users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
        included_categories = []
        included_categories.append(self.env["product.category"].search([("name", "=", "Videogiochi")]).id)
        included_categories.append(self.env["product.category"].search([("name", "=", "Gadget")]).id)
        included_categories.append(self.env["product.category"].search([("name", "=", "Figures")]).id)
        included_categories.append(self.env["product.category"].search([("name", "=", "Modellismo e Model Kit")]).id)
        if self.categ_id.id in included_categories:
            users_2 = "andrea.alunni@netaddiction.it, riccardo.ioni@netaddiction.it"
            if self.visible:
                obj = "[SHOPPING] PRODOTTO ACCESO [%s] %s id: %s" % (self.categ_id.name, self.name, self.id)
            else:
                obj = "[SHOPPING] PRODOTTO SPENTO [%s] %s id: %s" % (self.categ_id.name, self.name, self.id)
            # self.env["netaddiction.email.dispatcher"].send_notification(obj, obj, "shopping@multiplayer.com", set(users))
            self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients(obj, obj, "shopping@multiplayer.com", users_2)

    @api.model
    def _verify_release_date(self):
        if self.env.context.get('skip_notification_mail', False):
            return
        # TODO risistemare acl per mail o fare menu di configurazione
        # users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        # users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
        users_2 = "andrea.alunni@netaddiction.it, riccardo.ioni@netaddiction.it"
        products_out = self.env["product.product"].search([("out_date", "=", date.today() + timedelta(days=7))])
        products_available = self.env["product.product"].search([("available_date", "=", date.today() + timedelta(days=7))])
        products_out_lst = []
        products_available_lst = []
        if products_out:
            for product in products_out:
                products_out_lst.append(" %s id: %s data uscita %s <br>" % (product.name, product.id, product.out_date))
            # self.env["netaddiction.email.dispatcher"].send_notification("".join(products_out_lst), "[SHOPPING] PRODOTTI IN USCITA ESATTAMENTE TRA 7 GIORNI", "shopping@multiplayer.com", set(users))
            self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients("".join(products_out_lst), "[SHOPPING] PRODOTTI IN USCITA ESATTAMENTE TRA 7 GIORNI", "shopping@multiplayer.com", users_2)
        if products_available_lst:
            for product in products_available:
                products_available_lst.append("%s id: %s data uscita %s <br>" % (product.name, product.id, product.available_date))
            # self.env["netaddiction.email.dispatcher"].send_notification("".join(products_available_lst), "[SHOPPING] PRODOTTI DISPONIBILI ESATTAMENTE TRA 7 GIORNI", "shopping@multiplayer.com", set(users))
            self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients("".join(products_out_lst), "[SHOPPING] PRODOTTI IN USCITA ESATTAMENTE TRA 7 GIORNI", "shopping@multiplayer.com", users_2)
