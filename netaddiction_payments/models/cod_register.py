# -*- coding: utf-8 -*-
import csv
import base64
import io
from float_compare import isclose
from openerp import models, fields, api
from openerp.exceptions import Warning
import logging

SDA = "Numero riferimento spedizione"
BRT = "Riferimenti"
MONEY_BRT = "Euro"
MONEY_SDA = "Importo contrassegno"

_logger = logging.getLogger(__name__)


def strip_keys(d):
    # funzione di utilità che per effettuare lo stip delle chiavi di un dizionario
    return {k.strip(): strip_keys(v)
            if isinstance(v, dict)
            else v
            for k, v in d.iteritems()}


class CoDRegister(models.TransientModel):
    _name = "netaddiction.cod.register"

    csv_file = fields.Binary('File')

    def set_order_cash_on_delivery(self, order_id, real_invoice=False):
        """ imposta l'ordine con id 'order_id' per essere pagato con contrassegno se l'ordine è in draft (bozza) o in sale (lavorazione).
            Crea una fattura e un pagamento per ogni spedizione. Aggiunge spese di contrassegno.
        """
        order = self.env["sale.order"].search([("id", "=", order_id)])
        if order:
            if order.state == 'draft':
                order.action_confirm()

            if order.state in ('sale', 'problem'):
                contrassegno = self.env.ref('netaddiction_payments.product_contrassegno')
                order.payment_method_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal').id
                inv_lst = []
                pick_lst = []

                for line in order.order_line:
                    # resetto la qty_to_invoice di tutte le linee
                    line.qty_to_invoice = 0
                for delivery in order.picking_ids:
                    pick_lst.append(delivery) 
                    # aggiungo i contrassegni
                    values = {
                        'order_id': order.id,
                        'name': contrassegno.name,
                        'product_uom_qty': 1,
                        'product_uom': contrassegno.uom_id.id,
                        'product_id': contrassegno.id,
                        'is_payment': True,
                    }
                    sol = self.env['sale.order.line'].create(values)
                    sol.product_id_change()
                    sol.qty_to_invoice = 0

                    for stock_move in delivery.move_lines_related:
                        self._set_order_to_invoice(stock_move, order)

                    self.set_delivery_to_invoice(delivery, order, contrassegno.id)

                    inv_lst += order.action_invoice_create()
                # aggiungo i pagamenti in contrassegno e li associo alle fatture
                cod_aj = self.env.ref('netaddiction_payments.contrassegno_journal')
                pay_inbound = self.env["account.payment.method"].search([("payment_type", "=", "inbound")])
                pay_inbound = pay_inbound[0] if isinstance(pay_inbound, list) else pay_inbound
                if cod_aj and pay_inbound:
                    cod_id = cod_aj.id
                    order.payment_method_id = cod_id
                    for inv in inv_lst:
                        name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
                        invoice = self.env['account.invoice'].search([("id", "=", inv)])
                        invoice.is_customer_invoice = real_invoice
                        if order.gift_discount > 0.0:
                            gift_value = self.env["netaddiction.gift_invoice_helper"].compute_gift_value(order.gift_discount, order.amount_total, invoice.amount_total)
                            self.env["netaddiction.gift_invoice_helper"].gift_to_invoice(gift_value, invoice)

                        payment = self.env["account.payment"].create({"partner_type": "customer", "partner_id": order.partner_id.id, "journal_id": cod_id, "amount": invoice.amount_total, "order_id": order.id, "state": 'draft', "payment_type": 'inbound', "payment_method_id": pay_inbound.id, "name": name, 'communication': order.name})

                        payment.invoice_ids = [(4, inv, None)]

                        invoice.signal_workflow('invoice_open')
                        # assegno pagamento a spedizione
                        pick = [p for p in pick_lst if (isclose(p.total_import, payment.amount, abs_tol=0.009) and not p.payment_id)]
                        if pick:
                            pick[0].payment_id = payment.id

            return True

        return False

    def _set_order_to_invoice(self, stock_move, order):
        """dato 'order' imposta qty_to_invoice alla quantità giusta solo per i prodotti che si trovano in 'stock_move'
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

    def set_delivery_to_invoice(self, pick, order, cod_id):
        """dato 'order' imposta qty_to_invoice per una spedizione e un contrassegno
        """
        lines = [line for line in order.order_line if line.is_delivery and line.price_unit == pick.carrier_price and line.qty_invoiced < line.product_uom_qty]

        if lines:
            lines[0].qty_to_invoice = 1

        lines = [line for line in order.order_line if line.product_id.id == cod_id and line.qty_invoiced < line.product_uom_qty]

        if lines:
            lines[0].qty_to_invoice = 1

    @api.multi
    def execute(self):
        if self.csv_file:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.DictReader(decodedIO, delimiter=';')
            # implementing the head-tail design pattern
            head = reader.next()
            head = strip_keys(head)
            is_brt = True if BRT in head else False
            key = BRT if is_brt else SDA
            money_key = MONEY_BRT if MONEY_BRT in head else MONEY_SDA

            warning_list = []
            _logger.warning(head )
            contrassegno = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal')

            self._check_line(head, warning_list, key, money_key, contrassegno, is_brt)

            for line in reader:
                # attenzione alle ultime due righe coi totali
                line = strip_keys(line)

                self._check_line(line, warning_list, key, money_key, contrassegno, is_brt)

            if warning_list:
                raise Warning("non sono stati trovati pagamenti in contrassegno per i seguenti ordini nel file: %s" % warning_list)

    def _check_line(self, line, warning_list, key, money_key, contrassegno, is_brt):
        found = False
        if line[key] and line[money_key]:
            _logger.warning("ci sono le linee")
            order = None
            if is_brt:
                order = self.env["sale.order"].search([("id", "=", line[key])])
            else:
                pick = self.env["stock.picking"].search([("id", "=", line[key])])
                order = pick.sale_id if pick else None
            if order:
                amount_str = line[money_key].replace(",", ".").replace("€", "")
                amount = float(amount_str)
                _logger.warning("ordine trovato %s amount %s" % (order.name, amount))

                for payment in order.account_payment_ids:

                    if (isclose(payment.amount, amount, abs_tol=0.009)) and payment.journal_id.id == contrassegno.id and not payment.state == 'posted':
                        _logger.warning("sto per fare il post del pagamento %s name %s" % (payment.id, payment.name))
                        try:
                            payment.post()
                        except Exception as e:
                            _logger.warning(e)
                            return
                        _logger.warning("post eseguito per pagamento %s payment state %s name %s" % (payment.id, payment.state, payment.name))
                        found = True
                        break
                if not found:
                    warning_list.append((order.name, line[key], amount_str))
                else:
                    all_paid = True
                    for p in order.account_payment_ids:
                        all_paid = all_paid and p.state == 'posted'
                    if all_paid:
                        order.date_done = fields.Datetime.now()
            else:
                warning_list.append((None, line[key], None))
        else:
            warning_list.append((None, key, None))
