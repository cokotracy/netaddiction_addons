# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class StockNotificationController(http.Controller):
    def _create_product_stock_notification(self, email, product_id):
        request.env["product.stock.notification"].sudo().create({"product_id": int(product_id), "email": email})
        return True

    @http.route("/shop/product/stock/notification", type="json", auth="public", website=True)
    def product_stock_notification(self, email, product_id):
        if email and product_id:
            if (
                request.env["product.stock.notification"]
                .sudo()
                .search([("product_id", "=", int(product_id)), ("email", "=", email)])
            ):
                return {
                    "status": "duplicate",
                    "message": "Già stai seguendo questo prodotto.",
                }
            self._create_product_stock_notification(email, product_id)
            return {
                "status": "success",
                "message": "Abbiamo ricevuto la sua richiesta,<br/> la informeremo quando il prodotto sarà disponibile.<br/>",
            }
        return {
            "status": "error",
            "message": "Si è verificato un errore durante l’elaborazione della richiesta.",
        }
