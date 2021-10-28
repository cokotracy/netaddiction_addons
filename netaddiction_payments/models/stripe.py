# Copyright 2021 Netaddiction s.r.l. (netaddiction.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
import stripe

from odoo import api, models, fields
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


STRIPE_DEFAULT_DECLINE_MESSAGE = "La sua carta non è stata autorizzata dal circuito bancario. Assicurati che nella carta ci sia almeno 1 euro di disponibilità."
STRIPE_CARD_DECLINE_MESSAGE = {
    "transaction_not_allowed": "La sua carta non supporta questo tipo di acquisto.",
    "incorrect_number": "Il numero della sua carta non è corretto.",
    "insufficient_funds": "La sua carta non ha fondi sufficienti.",
    "expired_card": "La sua carta è scaduta.",
    "do_not_honor": "La sua carta non è stata autorizzata dal circuito bancario.",
}

INT_CURRENCIES = [
    "BIF",
    "XAF",
    "XPF",
    "CLP",
    "KMF",
    "DJF",
    "GNF",
    "JPY",
    "MGA",
    "PYG",
    "RWF",
    "KRW",
    "VUV",
    "VND",
    "XOF",
]


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

    def create_setup_intent(self, data):
        stripe.api_key = self.sudo().netaddiction_stripe_sk
        card_token = data.get("token")
        partner = data.get("partner_id")
        payment_method = self._get_payment_method(card_token)
        customer = self._get_or_create_customer(partner)
        if payment_method:
            return stripe.SetupIntent.create(
                customer=customer,
                payment_method=payment_method,
                payment_method_options={"card": {"request_three_d_secure": "any"}},
            )

    @api.model
    def get_payments_token(self, data):
        results = []
        for token in self.env["payment.token"].search(
            [("acquirer_id", "=", int(data["acquirer_id"])), ("partner_id", "=", int(data["partner_id"]))]
        ):
            results.append(
                {
                    "id": token.id,
                    "brand": token.brand.lower(),
                    "last4": token.name.strip("X"),
                    "isDefault": token.default_payment,
                }
            )
        return results

    @api.model
    def create_payment_token(self, data):
        stripe.api_key = self.sudo().netaddiction_stripe_sk
        card_token = data.get("token")
        partner = data.get("partner_id")
        customer = self._get_or_create_customer(partner)
        try:
            card = self._get_or_create_association_cc(card_token["id"], customer)
        except stripe.error.CardError as e:
            _logger.error(f"Stripe Card Error: A error encountered : {e.user_message}")
            return {
                "result": False,
                "error": {"message": self._get_translated_message(e.error.get("decline_code", ""))},
            }
        except Exception as e:
            _logger.error(f"Stripe Generic Error: A error encountered : {e}")
            return {
                "result": False,
                "error": {
                    "message": "Impossibile aggiungere la carta di credito.",
                },
            }

        if self.env["payment.token"].sudo().search([("netaddiction_stripe_payment_method", "=", card["id"])]):
            return {
                "result": False,
                "error": {
                    "message": "La seguente carta è già presente nella lista delle dei tuoi metodi di pagamento.",
                },
            }
        payment_token = (
            self.env["payment.token"]
            .sudo()
            .create(
                {
                    "acquirer_id": int(data["acquirer_id"]),
                    "partner_id": partner.id,
                    "netaddiction_stripe_payment_method": card["id"],
                    "name": f"XXXXXXXXXXXX{card.get('last4', '****')}",
                    "brand": card.get("brand", ""),
                    "acquirer_ref": customer,
                }
            )
        )
        payment_token.verified = True

        if (
            not self.env["payment.token"]
            .sudo()
            .search([("partner_id", "=", partner.id), ("default_payment", "=", True)])
        ):
            payment_token.default_payment = True

        return {
            "result": True,
            "token": payment_token.id,
        }

    def set_default_payment(self, data):
        partner = data.get("partner_id")
        payment_token = data.get("token")
        payments = (
            self.env["payment.token"].sudo().search([("partner_id", "=", partner.id), ("default_payment", "=", True)])
        )
        payments.default_payment = False
        self.env["payment.token"].sudo().search([("id", "=", payment_token)]).default_payment = True

        return {
            "result": True,
        }

    def _get_or_create_customer(self, partner):
        stripe.api_key = self.sudo().netaddiction_stripe_sk
        customer = stripe.Customer.list(email=partner.email)
        if not customer:
            c_name = partner.name if partner.name else partner.id
            customer = stripe.Customer.create(name=c_name, email=partner.email)
            return customer["id"]
        else:
            return customer.data[0]["id"]

    def _get_or_create_association_cc(self, token, customer_id):
        stripe.api_key = self.sudo().netaddiction_stripe_sk
        current_card = stripe.Token.retrieve(token)
        cards = stripe.Customer.list_sources(customer_id, object="card")
        source = None
        for card in cards.data:
            if card.fingerprint == current_card.card.fingerprint:
                source = card
        if not source:
            source = stripe.Customer.create_source(
                customer_id,
                source=token,
            )
        return source

    def _get_payment_method(self, token):
        payment = self.env["payment.token"].sudo().search([("id", "=", token)])
        if payment:
            return payment.netaddiction_stripe_payment_method

    def _get_translated_message(self, decline_code):
        return STRIPE_CARD_DECLINE_MESSAGE.get(decline_code, STRIPE_DEFAULT_DECLINE_MESSAGE)


class StripePaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def ns_do_transaction(self):
        self.ensure_one()
        result = self._ns_create_payment_intent()
        return self._ns_validate_response(result)

    def get_ns_payment_from_order(self, order):
        for payment in order.transaction_ids:
            if payment.payment_id.state != "posted" and payment.acquirer_id.provider == "netaddiction_stripe":
                return payment

    def _ns_create_payment_intent(self):
        stripe.api_key = self.acquirer_id.sudo().netaddiction_stripe_sk
        try:
            res = stripe.PaymentIntent.create(
                amount=int(
                    self.amount if self.currency_id.name in INT_CURRENCIES else float_round(self.amount * 100, 2)
                ),
                currency="eur",
                off_session=True,
                confirm=True,
                payment_method=self.payment_token_id.netaddiction_stripe_payment_method,
                customer=self.payment_token_id.acquirer_ref,
                description=f"Ordine numero: {self.reference}",
            )
        except stripe.error.CardError as e:
            _logger.error(f"Stripe Card Error: A error encountered : {e.user_message}")
            return {"status": e.code, "failure_message": e.user_message}
        except Exception as e:
            _logger.error(f"Stripe Generic Error: A error encountered : {e}")
            return {"status": "error", "failure_message": "Errore generico"}
        else:
            if res.get("charges") and res.get("charges").get("total_count"):
                res = res.get("charges").get("data")[0]
            return res

    def _ns_validate_response(self, response):
        self.ensure_one()
        if self.state not in ("draft", "pending"):
            return True
        status = response.get("status")
        tx_id = response.get("id")
        vals = {
            "date": fields.datetime.now(),
            "acquirer_reference": tx_id,
        }
        if status == "succeeded":
            self.write(vals)
            self._set_transaction_done()
            return True
        if status == "requires_action":
            self.write(vals)
            self._set_transaction_error("Richiesta azione manuale")
            return False
        else:
            error = response.get("failure_message")
            self._set_transaction_error(error)
            return False


class StripePaymentToken(models.Model):
    _inherit = "payment.token"

    netaddiction_stripe_payment_method = fields.Char("Payment Method ID")
    default_payment = fields.Boolean("Carta predefinita ?", default=False)
    brand = fields.Char("Brand della carta")
