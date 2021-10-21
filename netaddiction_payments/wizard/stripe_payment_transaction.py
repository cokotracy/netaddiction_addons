from datetime import datetime

from odoo import fields, models
from odoo.exceptions import UserError


class StripeCreatePaymentTransaction(models.TransientModel):
    _name = "stripe.create.payment.transaction"
    _description = "Modello Transient per creare manualmente una transazione con Stripe."

    def _get_current_order(self):
        active_id = self.env.context.get("active_id", [])
        return self.env["sale.order"].search([("id", "=", active_id)])

    def _default_payment(self):
        current_order = self._get_current_order()
        if not current_order:
            return
        partner_tokens = self.env["payment.token"].search([("partner_id", "=", current_order.partner_id.id)])
        if partner_tokens:
            for token in partner_tokens:
                if token.default_payment:
                    return token.id
            return partner_tokens[0].id

    def _domain_payment_token(self):
        current_order = self._get_current_order()
        if current_order:
            return [("partner_id", "=", current_order.partner_id.id)]
        return []

    def _validate_order(self, order):
        if order.state not in ["draft"]:
            raise UserError("Impossibile generare il pagamento: Lo stato dell'ordine non è in 'preventivo'")
        for tx in order.transaction_ids:
            if tx.state == "draft" and tx.acquirer_id.provider == "netaddiction_stripe":
                raise UserError("Impossibile generare il pagamento: Esiste già un pagamento con Stripe")

    payment_token_id = fields.Many2one(
        "payment.token",
        string="Carta di Credito/Debito",
        default=_default_payment,
        domain=_domain_payment_token,
        required=True,
    )

    def do_action(self):
        order = self._get_current_order()
        if not order:
            raise UserError("Impossibile trovare l'ordine corrente.")
        if not self.payment_token_id:
            raise UserError("Nessuna carta di credito/debito trovata.")
        self._validate_order(order)

        # create transaction
        vals = {"payment_token_id": self.payment_token_id.id, "return_url": "/shop/payment/validate"}
        tx = order._create_payment_transaction(vals)
        if tx.acquirer_id.provider == "netaddiction_stripe":
            payment = tx._create_payment()
            payment.state = "draft"
            vals = {
                "date": datetime.now(),
                "acquirer_id": tx.acquirer_id.id,
                "partner_id": tx.partner_id.id,
                "payment_id": payment.id,
            }
            tx.write(vals)
