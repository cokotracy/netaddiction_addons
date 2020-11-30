# -*- coding: utf-8 -*-
import stripe
import payment_exception
import cypher

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from float_compare import isclose


class CardExist(Exception):
    def __init__(self, msg='Questa carta di credito è già associata al tuo account', *args, **kwargs):
        super(Exception, self).__init__(msg, *args, **kwargs)


class StripeExecutor(models.TransientModel):
    """
    Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con Stripe
    """
    _name = "netaddiction.stripe.executor"

    CardExist = CardExist

    def get_stripe_public_key(self):
        encripted_pub_key = self.env["ir.values"].search(
            [("name", "=", "stripe_public_key")]).value

        key = self.env["ir.config_parameter"].search(
            [("key", "=", "stripe.key")]).value

        return cypher.decrypt(key, encripted_pub_key)

    def get_stripe_secret_key(self):
        encripted_priv_key = self.env["ir.values"].search(
            [("name", "=", "stripe_private_key")]).value

        key = self.env["ir.config_parameter"].search(
            [("key", "=", "stripe.key")]).value

        return cypher.decrypt(key, encripted_priv_key)

    def get_customer_or_create(self, name, email):
        stripe.api_key = self.get_stripe_secret_key()
        customer = stripe.Customer.list(email=email)
        if not customer:
            customer = stripe.Customer.create(
                name=name,
                email=email
            )
            return customer['id']
        else:
            return customer.data[0]["id"]

    def get_payment_secret(self, p_id):
        stripe.api_key = self.get_stripe_secret_key()
        payment_intent = stripe.PaymentIntent.retrieve(p_id)
        if payment_intent:
            return payment_intent.client_secret, payment_intent.last_payment_error.payment_method.id

    def check_cc_or_create(self, token, last_four, exp_month, exp_year, partner_id, brand, card_holder):
        token_card = self.env["netaddiction.partner.ccdata"].search(
            [("token", "=", token)])
        if token_card:
            raise self.CardExist
        else:
            last_four = 'XXXXXXXXXXXX{}'.format(last_four)
            return self.env["netaddiction.partner.ccdata"].create({'token': token, 'month': exp_month, 'year': exp_year, 'name': card_holder, 'last_four': last_four, 'customer_id': partner_id, 'ctype': brand})

    def check_association_cc(self, token, customer_id):
        # Controllo se il cliente ha associata la carta, su Stripe, altrimenti la creo e l'associo
        current_card = stripe.Token.retrieve(token)
        cards = stripe.Customer.list_sources(
            customer_id,
            object='card'
        )
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

    def token_delete(self, partner_mail, token):
        stripe.api_key = self.get_stripe_secret_key()

        # Ricavo il cliente da Stripe tramite la sua mail
        customer = stripe.Customer.list(email=partner_mail)
        if customer:
            return stripe.Customer.delete_source(
                customer.data[0]["id"],
                token,
            )

    def setup_intent(self, customer_id, cc_token):
        stripe.api_key = self.get_stripe_secret_key()

        # Creo il SetupIntent
        return stripe.SetupIntent.create(
            customer=customer_id,
            payment_method=cc_token
        )

    def complete_payment(self, token, order_id, real_invoice=False):
        try:
            self._generate_invoice_payment(order_id, token, real_invoice)
        except Exception as e:
            return e
        return True

    def auth_and_check(self, partner_id, partner_email, amount, token, order_id):
        """
        Metodo che si interfaccia con Stripe per effettuare una autorizzazione e conferma di un pagamento.
        Se l'operazione ha successo, viene cambiato lo stato status della cc in confirm nel pagamento corrispondente nell'ordine di id = order_id. Se non viene trovato un pagamento corrispondente ne crea uno.
        """
        stripe.api_key = self.get_stripe_secret_key()
        order, cc_journal, payment = self._check_payment(order_id, amount)
        vc_amount = int(amount * 100)
        customer = stripe.Customer.list(email=partner_email)
        try:
            payint = stripe.PaymentIntent.create(
                amount=vc_amount,
                currency='eur',
                customer=customer.data[0]["id"],
                payment_method=token,
                off_session=True,
                confirm=True,
                metadata={
                    'order_id': order.name
                }

            )
        except stripe.error.CardError as e:
            if e.code == 'authentication_required':
                payment_intent_id = e.error.payment_intent['id']
                # TODO Da ricontrollare
                order.state = 'problem'
                self._send_3ds_auth_mail(
                    partner_email, order.id, order.name, payment_intent_id)
            raise payment_exception.PaymentException(
                payment_exception.CREDITCARD, "%s" % e)
        except Exception as e:
            raise payment_exception.PaymentException(
                payment_exception.CREDITCARD, "%s" % e)
        else:
            self._set_payment_or_create(
                'posted', order, amount, payint.id, token, cc_journal)
            return payint

    def _generate_invoice_payment(self, order_id, token, real_invoice=False):
        order = self.env["sale.order"].search([("id", "=", order_id)])

        if order:
            if order.state == 'draft':
                order.action_confirm()

            if order.state in ('sale', 'problem'):
                cc_journal = self.env['ir.model.data'].get_object(
                    'netaddiction_payments', 'cc_journal')
                token_card = self.env["netaddiction.partner.ccdata"].search(
                    [("token", "=", token)])
                inv_lst = []
                pick_lst = []

                for line in order.order_line:
                    # resetto la qty_to_invoice di tutte le linee
                    line.qty_to_invoice = 0
                for delivery in order.picking_ids:
                    pick_lst.append(delivery)
                    for stock_move in delivery.move_lines_related:
                        self._set_order_to_invoice(stock_move, order)

                    self._set_delivery_to_invoice(delivery, order)

                    inv_lst += order.action_invoice_create()

                pay_inbound = self.env["account.payment.method"].search(
                    [("payment_type", "=", "inbound")])
                pay_inbound = pay_inbound[0] if isinstance(
                    pay_inbound, list) else pay_inbound

                if cc_journal and pay_inbound:

                    cc_journal_id = cc_journal.id
                    order.payment_method_id = cc_journal_id
                    for inv in inv_lst:
                        name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(
                            self)).next_by_code('account.payment.customer.invoice')
                        invoice = self.env['account.invoice'].search(
                            [("id", "=", inv)])
                        invoice.is_customer_invoice = real_invoice
                        if order.gift_discount > 0.0:
                            gift_value = self.env["netaddiction.gift_invoice_helper"].compute_gift_value(
                                order.gift_discount, order.amount_total, invoice.amount_total)
                            self.env["netaddiction.gift_invoice_helper"].gift_to_invoice(
                                gift_value, invoice)

                        if not isclose(order.amount_total, 0.0000, abs_tol=0.009):

                            # una spedizione potrebbe essere anche a costo zero, in quel caso non ci sono pagamenti
                            payment = self.env["account.payment"].create({"partner_type": "customer", "partner_id": order.partner_id.id, "journal_id": cc_journal_id, "amount": invoice.amount_total, "order_id": order.id, "state": 'draft', "payment_type": 'inbound', "payment_method_id": pay_inbound.id,
                                                                          "name": name, 'communication': order.name, 'cc_token': token, 'cc_last_four': token_card.last_four, 'cc_month': token_card.month, 'cc_year': token_card.year, 'cc_name': token_card.name, 'cc_status': 'init', 'cc_type': token_card.ctype})

                            payment.invoice_ids = [(4, inv, None)]
                            # associo la spedizione al pagamento
                            pick = [p for p in pick_lst if (
                                isclose(p.total_import, payment.amount, abs_tol=0.009) and not p.payment_id)]
                            if pick:
                                pick[0].payment_id = payment.id

                        invoice.signal_workflow('invoice_open')
        else:
            raise payment_exception.PaymentException(
                payment_exception.CREDITCARD, "impossibile trovare l'ordine %s" % order_id)

    def _set_order_to_invoice(self, stock_move, order):
        """
        dato 'order' imposta qty_to_invoice alla quantità giusta solo per i prodotti che si trovano in 'stock_move'
        """
        prod_id = stock_move.product_id
        qty = stock_move.product_uom_qty

        lines = [line for line in order.order_line if line.product_id == prod_id]
        for line in lines:
            qty_to_invoice = qty if qty < line.product_uom_qty else line.product_uom_qty

            line.qty_to_invoice += qty_to_invoice

            qty = qty - qty_to_invoice

            if qty <= 0:
                break

    def _set_delivery_to_invoice(self, pick, order):
        """
        dato 'order' imposta qty_to_invoice per una spedizione
        """
        lines = [line for line in order.order_line if line.is_delivery and line.price_unit ==
                 pick.carrier_price and line.qty_invoiced < line.product_uom_qty]

        if lines:
            lines[0].qty_to_invoice = 1

    def _set_payment_or_create(self, state, order, amount, tranID, token, cc_journal):

        found = False
        for payment in order.account_payment_ids:
            if (isclose(payment.amount, amount, abs_tol=0.009)) and payment.journal_id.id == cc_journal.id and not payment.state == 'posted':
                found = True
                payment.cc_tran_id = tranID
                if state == 'auth':
                    payment.cc_status = state
                elif state == 'posted':
                    payment.cc_status = 'commit'
                    payment.delay_post()
                break
        if not found:
            # non ho trovato un pagamento da associare, ne creo uno (la situazione richiederà un intervento manuale)
            name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(
                self)).next_by_code('account.payment.customer.invoice')
            pay_inbound = self.env["account.payment.method"].search(
                [("payment_type", "=", "inbound")])
            pay_inbound = pay_inbound[0] if isinstance(
                pay_inbound, list) else pay_inbound
            token_card = self.env["netaddiction.partner.ccdata"].search(
                [("token", "=", token)])
            payment = self.env["account.payment"].create({"partner_type": "customer", "partner_id": order.partner_id.id, "journal_id": cc_journal.id, "amount": amount, "order_id": order.id, "state": state, "payment_type": 'inbound', "payment_method_id": pay_inbound.id, "name": name, 'communication': (
                "PAGAMENTO SENZA FATTURA CREATO DURANTE %s CC" % state), 'token': token, 'last_four': token_card.last_four, 'month': token_card.month, 'year': token_card.year, 'name': token_card.name, 'cc_status': 'auth', 'cc_tran_id': tranID})

    def _check_payment(self, order_id, amount):
        order = self.env["sale.order"].search([("id", "=", order_id)])
        cc_journal = self.env['ir.model.data'].get_object(
            'netaddiction_payments', 'cc_journal')
        found = False

        if not order:
            raise payment_exception.PaymentException(
                payment_exception.CREDITCARD, "impossibile trovare l'ordine %s" % order_id)

        for payment in order.account_payment_ids:
            if (isclose(payment.amount, amount, abs_tol=0.009)) and payment.journal_id.id == cc_journal.id and not payment.state == 'posted':
                found = True
                break
        if found:
            return (order, cc_journal, payment)
        else:
            raise payment_exception.PaymentException(
                payment_exception.CREDITCARD, "nessun pagamento corrispondente a %s trovato nell'ordine %s" % (amount, order_id))

    def _get_customer_care_settings(self):
        to_search = [('company_id', '=', 1)]
        res = self.env['netaddiction.project.issue.settings.companymail'].search(
            to_search)
        return res

    def _get_email_from(self):
        res = self._get_customer_care_settings()
        return res.email

    def _get_template_email(self):
        res = self._get_customer_care_settings()
        return res.template_email

    def _send_3ds_auth_mail(self, mail_to, order_id, order_name, payment_intent_id):
        template = self._get_template_email()

        link = 'https://staging2.multiplayer.com/account/ordini/%s/3ds-authentication/?payment_intent_id=%s' % (
            order_id, payment_intent_id)
        message = '''
        <span style="font-size: 16px;">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse vitae fringilla sapien, nec iaculis neque.</span> <br><br>
        <a href="%s" style="display: block; padding: 20px; text-align: center; background-color: #295F8F; font-size: 24px; font-weight: bold; color: #fff; border-radius: 5px">Autorizza il pagamento dell'ordine</a>
        ''' % link

        body = template.replace('[TAG_BODY]', message)

        mail = {
            'subject': '[%s] Multiplayer.com - Richiesta Autorizzazione 3DS' % (order_name),
            'email_from': self._get_email_from(),
            'reply_to': self._get_email_from(),
            'email_to': mail_to,
            'body_html': body,
            'model': 'project.issue',
        }

        email = self.env['mail.mail'].create(mail)
        email.send()
