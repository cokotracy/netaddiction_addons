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
        vals = {"payment_token_id": pm_id, "return_url": "/shop/payment/validate"}

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
            result = request.render("website_sale.confirmation", {"order": order})
            affiliate_module = request.env["ir.module.module"].sudo().search([("name", "=", "affiliate_management")])
            if affiliate_module and affiliate_module.state == "installed":
                return self._update_affiliate_visit_cookies(order, result)
            return result
        else:
            return request.redirect("/payment/process")

    def _update_affiliate_visit_cookies(self, sale_order_id, result):
        """update affiliate.visit from cokkies data i.e created in product and shop method"""
        cookies = dict(request.httprequest.cookies)
        visit = request.env["affiliate.visit"]
        arr = []  # contains cookies product_id
        for k, v in cookies.items():
            if "affkey_" in k:
                arr.append(k.split("_")[1])
        if arr:
            partner_id = (
                request.env["res.partner"]
                .sudo()
                .search([("res_affiliate_key", "=", arr[0]), ("is_affiliate", "=", True)])
            )
            for s in sale_order_id.order_line:
                if s.product_id.type != "service" and len(arr) > 0 and partner_id:
                    product_tmpl_id = s.product_id.product_tmpl_id.id
                    aff_visit = visit.sudo().create(
                        {
                            "affiliate_method": "pps",
                            "affiliate_key": arr[0],
                            "affiliate_partner_id": partner_id.id,
                            "url": "",
                            "ip_address": request.httprequest.environ["REMOTE_ADDR"],
                            "type_id": product_tmpl_id,
                            "affiliate_type": "product",
                            "type_name": s.product_id.id,
                            "sales_order_line_id": s.id,
                            "convert_date": fields.datetime.now(),
                            "affiliate_program_id": partner_id.affiliate_program_id.id,
                            "product_quantity": s.product_uom_qty,
                            "is_converted": True,
                        }
                    )
            # delete cookie after first sale occur
            cookie_del_status = False
            for k, v in cookies.items():
                if "affkey_" in k:
                    cookie_del_status = result.delete_cookie(key=k)
        return result


class NetaddictionStripeController(http.Controller):
    @http.route(["/netaddiction_stripe/payment/feedback"], type="http", auth="none", csrf=False)
    def netaddiction_stripe_form_feedback(self, **post):
        post.update({"return_url": "/shop/payment/validate"})

        request.env["payment.transaction"].sudo().form_feedback(post, "netaddiction_stripe")
        return werkzeug.utils.redirect(post.pop("return_url", "/"))

    @http.route("/payment/netaddiction-stripe/create-setup-intent", type="json", auth="public", csrf=False)
    def create_setup_intent(self, **kwargs):
        if not kwargs.get("partner_id"):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id)
        res = request.env["payment.acquirer"].browse(int(kwargs.get("acquirer_id"))).create_setup_intent(kwargs)
        return res.get("client_secret")

    @http.route(["/payment/netaddiction-stripe/get-payments-token"], type="json", auth="public", csrf=False)
    def get_payments_token(self, **kwargs):
        if not kwargs.get("partner_id"):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
        tokens = request.env["payment.acquirer"].browse(int(kwargs.get("acquirer_id"))).get_payments_token(kwargs)
        return tokens

    @http.route(["/payment/netaddiction-stripe/create-payment-token"], type="json", auth="public", csrf=False)
    def create_payment_token(self, **kwargs):
        if not kwargs.get("partner_id"):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id)
        res = request.env["payment.acquirer"].browse(int(kwargs.get("acquirer_id"))).create_payment_token(kwargs)
        return res

    @http.route(["/payment/netaddiction-stripe/set-default-payment"], type="json", auth="public", csrf=False)
    def set_default_payment(self, **kwargs):
        if not kwargs.get("partner_id"):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id)
        res = request.env["payment.acquirer"].browse(int(kwargs.get("acquirer_id"))).set_default_payment(kwargs)
        return res
