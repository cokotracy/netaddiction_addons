# Copyright 2021 Netaddiction s.r.l. (netaddiction.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
import stripe

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


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

    def netaddiction_stripe_get_form_action_url(self):
        return "/netaddiction_stripe/payment/feedback"

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

    @api.model
    def create_payment_token(self, data):
        stripe.api_key = self.sudo().netaddiction_stripe_sk
        res = stripe.PaymentMethod.retrieve(data.get("payment_method"))
        token = (
            self.env["payment.token"]
            .sudo()
            .search([("netaddiction_stripe_payment_method", "=", data.get("payment_method"))])
        )
        if token:
            return token
        card = res.get("card", {})
        if card:
            payment_token = (
                self.env["payment.token"]
                .sudo()
                .create(
                    {
                        "acquirer_id": int(data["acquirer_id"]),
                        "partner_id": int(data["partner_id"]),
                        "netaddiction_stripe_payment_method": data.get("payment_method"),
                        "name": f"XXXXXXXXXXXX{card.get('last4', '****')}",
                        "brand": card.get("brand", ""),
                        "acquirer_ref": f"stripe_{int(data['acquirer_id'])}",
                        "active": False,
                    }
                )
            )
            return payment_token


class StripePaymentTransaction(models.Model):
    _inherit = "payment.transaction"


class StripePaymentToken(models.Model):
    _inherit = "payment.token"

    netaddiction_stripe_payment_method = fields.Char("Payment Method ID")
    default_payment = fields.Boolean("Carta predefinita ?", default=False)
    brand = fields.Char("Brand della carta")
