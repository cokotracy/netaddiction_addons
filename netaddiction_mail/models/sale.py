# -*- coding: utf-8 -*-

from openerp import api, models


class Order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_cancel(self):

        users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_products_data_entry_user_manager")
        users += self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_sale_user_manager")
        categories = [line.product_id.categ_id.name for line in self.order_line]
        obj = "[SHOPPING] ANNULLATO ordine %s %s" % (self.name, ", ".join(set(categories)))
        self.env["netaddiction.email.dispatcher"].send_mail(obj, obj, "shopping@multiplayer.com", set(users))

        super(Order, self).action_cancel()
