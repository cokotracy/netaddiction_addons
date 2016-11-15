# -*- coding: utf-8 -*-

from openerp import api, models, fields
from datetime import timedelta
import payment_exception
import sofort
import cypher


class SofortExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con cc tramite bnl positivity, e per registrare carte di credito da BO in maniera sicura
    """
    _name = "netaddiction.sofort.executor"

    real_invoice = fields.Boolean(default=False)
    sofort_transaction_id = fields.Char(string='ID transazione sofort')

    def initiate_payment(self, success_url, abort_url, default_url, order, amount, real_invoice=False):
        """

        Primo metodo da chiamare per effettuare un pagamento su Sofort
            Parametri:
            -amount: quantità da pagare, IMPORTANTE: COMPRESE SPESE DI SPEDIZIONE
            -success_url: url a cui reindirizzare l'utente in caso di successo nel pagamento sofort
            -abort_url: url a cui reindirizzare l'utente in caso di fallimento nel pagamento sofort
            -default_url: url su cui ricevere la risposta da sofort. deve essere tipo 'http://9f372dbc.ngrok.io/bnl.php?trn={0}' con parametro 'trn' che  inserisce il metodo e che sarà restituito da sofort all'url indicato
            -order: l'ordine
            -[real_invoice]: true se il cliente vuole la fattura
            Returns:
            -se tutto ok: un dizionario con chiavi
                'url' : url da tornare al cliente per pagare
                'transaction_id' : id della transazione sofort --> da controllare col valore tornato da sofort tramite POST
            -False altrimenti
            -Raise PaymentException se ci sono problemi a registrare il pagamento
        """

        encripted_username = self.env["ir.values"].search([("name", "=", "sofort_username")]).value
        encripted_apikey = self.env["ir.values"].search([("name", "=", "sofort_apikey")]).value
        encripted_project = self.env["ir.values"].search([("name", "=", "sofort_project")]).value

        key = self.env["ir.config_parameter"].search([("key", "=", "sofort.key")]).value

        username = cypher.decrypt(key, encripted_username)
        apikey = cypher.decrypt(key, encripted_apikey)
        project = cypher.decrypt(key, encripted_project)

        client = sofort.Client(username, apikey, project,
            success_url=success_url,
            abort_url=abort_url,
            country_code='IT',
            notification_urls={
                'default': default_url.format(sofort.TRANSACTION_ID),
            },
        )

        t = client.payment(
            amount,
            reasons=[
                "Ordine %s" % order.name,
            ]
        )
        if t:
            self.real_invoice = real_invoice
            pp_aj = self.env['ir.model.data'].get_object('netaddiction_payments', 'sofort_journal')
            pay_inbound = self.env["account.payment.method"].search([("payment_type", "=", "inbound")])
            pay_inbound = pay_inbound[0] if isinstance(pay_inbound, list) else pay_inbound
            if pp_aj and pay_inbound:
                name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
                pp_id = pp_aj.id
                payment = self.env["account.payment"].create({
                    "partner_type": "customer",
                    "partner_id": order.partner_id.id,
                    "journal_id": pp_id,
                    "amount": amount,
                    "order_id": order.id,
                    "state": 'draft',
                    "payment_type": 'inbound',
                    "payment_method_id": pay_inbound.id,
                    "name": name,
                    'communication': order.name,
                    'sofort_transaction_id': t.transaction,

                })

                order.payment_method_id = pp_aj.id
                order.state = 'pending'
                self.sofort_transaction_id = t.transaction
                return {
                    'url': t.payment_url,
                    'transaction_id': t.transaction
                }

            else:
                raise payment_exception.PaymentException(payment_exception.SOFORT, "impossibile trovare il metodo di pagamento Sofort")
        else:
            return False

    def register_payment(self):
        """
        metodo per registrare il pagamento sofort
        Returns:
            - se tutto ok: True
            - altrimenti: False
        """
        payments = self.env['account.payment'].search([
            ('state', '=', 'draft'),
            ('sofort_transaction_id', '=', self.sofort_transaction_id),
        ])

        if not payments:
            return False

        for payment in payments:

            order = payment.order_id
            order.state = 'draft'
            order.action_confirm()

            self._set_order_to_invoice(order)

            inv_lst = order.action_invoice_create()

            payment.invoice_ids = [(4, inv, None) for inv in inv_lst]

            for inv_id in inv_lst:
                inv = self.env["account.invoice"].search([("id", "=", inv_id)])
                inv.is_customer_invoice = self.real_invoice
                if order.gift_discount > 0.0:
                    gift_value = self.env["netaddiction.gift_invoice_helper"].compute_gift_value(order.gift_discount, order.amount_total, inv.amount_total)
                    self.env["netaddiction.gift_invoice_helper"].gift_to_invoice(gift_value, inv)
                inv.signal_workflow('invoice_open')
                # inv.payement_id = [(6, 0, [payment.id])]

            # assegno il pagamento alle spedizioni
            for delivery in order.picking_ids:
                delivery.payment_id = payment.id

            payment.delay_post()

        return True

    def _set_order_to_invoice(self, order):
        for line in order.order_line:
            line.qty_to_invoice = line.product_uom_qty

    # CRON CANCELLAZIONE PENDING SOFORT
    # @api.model
    # def _search_pending_sofort(self):
    #     pp_aj = self.env['ir.model.data'].get_object('netaddiction_payments', 'sofort_journal')
    #     order_list = self.env["sale.order"].search([("payment_method_id", "=", pp_aj.id), ("state", "=", "pending"), ("date_order", "<", (fields.Datetime.now() - timedelta(hours=2)).strftime("%d/%m/%Y %H:%M:%S"))])
    #     print order_list
    #     for order in order_list:
    #         order.action_cancel()
