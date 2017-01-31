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

        pp_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal')
        sofort_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'sofort_journal')

        if self.created_by_the_customer and self.state not in ["draft, done, pending"] and self.payment_method_id.id in [pp_journal.id, sofort_journal.id]:
            obj = "[SHOPPING] PAGAMENTO ANNULLATO RIMBORSO DA FARE ordine %s %s" % (self.name, ", ".join(set(categories)))
            users_2 = "shopping@multiplayer.com, riccardo.ioni@netaddiction.it"
            transaction_id = self.pay_pal_tran_id if self.pay_pal_tran_id else None
            for payment in self.account_payment_ids:
                if payment.journal_id.id == pp_journal.id:
                    transaction_id = payment.paypal_transaction_id
                    break

            self.env["netaddiction.email.dispatcher"].send_mail_fixed_recipients("ID transazione %s" % transaction_id, obj, "shopping@multiplayer.com", users_2)

        super(Order, self).action_cancel()
