# -*- coding: utf-8 -*-
import logging
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class NetaddictionStripeController(http.Controller):
    @http.route("/payment/netaddiction-stripe/create-setup-intent", type="json", auth="public", csrf=False)
    def create_setup_intent(self, acquirer_id):
        acquirer = request.env["payment.acquirer"].browse(int(acquirer_id))
        res = acquirer.with_context(stripe_manual_payment=True).create_setup_intent(request.env.user)
        return res.get("client_secret")

    # @http.route(["/payment/stripe/s2s/create_json_3ds"], type="json", auth="public", csrf=False)
    # def stripe_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
    #     if not kwargs.get("partner_id"):
    #         kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
    #     token = (
    #         request.env["payment.acquirer"]
    #         .browse(int(kwargs.get("acquirer_id")))
    #         .with_context(stripe_manual_payment=True)
    #         .s2s_process(kwargs)
    #     )

    #     if not token:
    #         res = {
    #             "result": False,
    #         }
    #         return res

    #     res = {
    #         "result": True,
    #         "id": token.id,
    #         "short_name": token.short_name,
    #         "3d_secure": False,
    #         "verified": False,
    #     }

    #     if verify_validity != False:
    #         token.validate()
    #         res["verified"] = token.verified

    #     return res
