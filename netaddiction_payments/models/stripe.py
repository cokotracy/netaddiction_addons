# Copyright 2021 Netaddiction s.r.l. (netaddiction.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import stripe

from odoo import models, fields


class CardExist(Exception):
    def __init__(self, msg="Questa carta di credito è già associata al tuo account", *args, **kwargs):
        super(CardExist, self).__init__(msg, *args, **kwargs)


class StripeAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("netaddiction_stripe", "Netaddiction Stripe")],
        ondelete={"netaddiction_stripe": "set default"},
    )
    netaddiction_stripe_pk = fields.Char(
        string="Chiave pubblica Stripe", required_if_provider="netaddiction_stripe", groups="base.group_user"
    )
    netaddiction_stripe_sk = fields.Char(
        string="Chiave privata Stripe", required_if_provider="netaddiction_stripe", groups="base.group_user"
    )

    def get_or_create_customer(self, user):
        stripe.api_key = self.sudo().netaddiction_stripe_sk
        customer = stripe.Customer.list(email=user.partner_id.email)
        if not customer:
            c_name = user.partner_id.name if user.partner_id.name else user.partner_id.id
            customer = stripe.Customer.create(name=c_name, email=user.partner_id.email)
            return customer["id"]
        else:
            return customer.data[0]["id"]

    def create_setup_intent(self, user):
        stripe.api_key = self.sudo().netaddiction_stripe_sk

        return stripe.SetupIntent.create(
            customer=self.get_or_create_customer(user),
            payment_method="card_1JiiAjHprgG5j0TdTQlCr44O",
            payment_method_options={"card": {"request_three_d_secure": "any"}},
        )
