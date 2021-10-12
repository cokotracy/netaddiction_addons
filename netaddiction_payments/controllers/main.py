# -*- coding: utf-8 -*-
import logging
import werkzeug

from datetime import datetime

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentProcessing

_logger = logging.getLogger(__name__)


class NetaddictionStripeSuper(WebsiteSale):
    @http.route("/shop/payment/token", type="http", auth="public", website=True, sitemap=False)
    def payment_token(self, pm_id=None, **kwargs):
        """Method that handles payment using saved tokens

        :param int pm_id: id of the payment.token that we want to use to pay.
        """
        order = request.website.sale_get_order()
        # do not crash if the user has already paid and try to pay again
        if not order:
            return request.redirect("/shop/?error=no_order")

        assert order.partner_id.id != request.website.partner_id.id

        try:
            pm_id = int(pm_id)
        except ValueError:
            return request.redirect("/shop/?error=invalid_token_id")

        # We retrieve the token the user want to use to pay
        if not request.env["payment.token"].sudo().search_count([("id", "=", pm_id)]):
            return request.redirect("/shop/?error=token_not_found")

        # Create transaction
        vals = {"payment_token_id": pm_id, "return_url": "/shop/paymento/validato"}

        tx = order._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(tx)

        if tx.acquirer_id.provider == "netaddiction_stripe":
            if not order or (order.amount_total and not tx):
                return request.redirect("/shop")

            payment = tx._create_payment()
            payment.state = "draft"
            vals = {
                "date": datetime.now(),
                "acquirer_id": tx.acquirer_id.id,
                "partner_id": tx.partner_id.id,
                "payment_id": payment.id,
            }
            tx.write(vals)
            tx.payment_token_id.verified = True

            order.with_context(send_email=True).action_confirm()
            order._send_order_confirmation_mail()
            request.website.sale_reset()
            return request.render("website_sale.confirmation", {"order": order})
        else:
            return request.redirect("/payment/process")


class NetaddictionStripeController(http.Controller):
    @http.route(["/netaddiction_stripe/payment/feedback"], type="http", auth="none", csrf=False)
    def netaddiction_stripe_form_feedback(self, **post):
        post.update({"return_url": "/shop/payment/validate"})

        request.env["payment.transaction"].sudo().form_feedback(post, "netaddiction_stripe")
        return werkzeug.utils.redirect(post.pop("return_url", "/"))

    @http.route("/payment/netaddiction-stripe/create-setup-intent", type="json", auth="public", csrf=False)
    def create_setup_intent(self, acquirer_id):
        acquirer = request.env["payment.acquirer"].browse(int(acquirer_id))
        res = acquirer.with_context(stripe_manual_payment=True).create_setup_intent(request.env.user)
        return res.get("client_secret")

    @http.route(["/payment/netaddiction-stripe/create-payment-token"], type="json", auth="public", csrf=False)
    def create_payment_token(self, **kwargs):
        if not kwargs.get("partner_id"):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
        token = (
            request.env["payment.acquirer"]
            .browse(int(kwargs.get("acquirer_id")))
            .with_context(stripe_manual_payment=True)
            .create_payment_token(kwargs)
        )

        if not token:
            res = {
                "result": False,
            }
            return res
        res = {
            "result": True,
            "id": token.id,
            "short_name": token.short_name,
            "3d_secure": True,
        }
        token.validate()
        res["verified"] = token.verified

        return res
