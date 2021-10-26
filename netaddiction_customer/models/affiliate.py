from odoo import models


class NetaddictionAffilitateVisit(models.TransientModel):
    _name = "netaddiction.affiliate.visit"

    def cron_confirm_affiliate_visit(self):
        visits = self.env["affiliate.visit"].search([("state", "=", "draft")])
        for visit in visits:
            try:
                visit.action_confirm()
                visit.write({"commission_type": "d"})
            except Exception:
                continue

    def _create_wallet_payment(self, affiliate, amount):
        wallet_transaction_obj = self.env["website.wallet.transaction"]

        balance = affiliate.wallet_balance + amount
        affiliate.write({"wallet_balance": balance})
        value = {
            "wallet_type": "credit",
            "reference": "manual",
            "amount": amount,
            "partner_id": affiliate.id,
            "currency_id": affiliate.property_product_pricelist.currency_id.id,
            "status": "done",
        }
        wallet_transaction_obj.sudo().create(value)

    def cron_affiliate_add_money_wallet(self):
        aff_visit_obj = self.env["affiliate.visit"]
        aff_orders = aff_visit_obj.search([("state", "=", "confirm"), ("id", "=", 1138)])
        for aff_order in aff_orders:
            order = aff_order.sales_order_line_id.order_id
            if order.state == "done" and (aff_order.commission_amt and aff_order.commission_amt > 0):
                try:
                    self._create_wallet_payment(aff_order.affiliate_partner_id, aff_order.commission_amt)
                except Exception:
                    continue
                else:
                    aff_order.write({"state": "paid"})
