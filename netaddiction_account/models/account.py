# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import csv
import io
import base64

from odoo import api, fields, models
from odoo.exceptions import UserError

HEAD_SDA = "Numero riferimento spedizione"
HEAD_BRT = "Riferimenti"
MONEY_SDA = "Importo contrassegno"
MONEY_BRT = "Euro"


class AccountInvoice(models.Model):

    _inherit = "account.move"

    create_credit_note = fields.Boolean("Crea una nota di credito")

    is_customer_invoice = fields.Boolean(string="Invoice")

    customer_number_identifier = fields.Char("Customer Number identifier", compute="_get_customer_number_identifier")

    @api.model
    def create(self, values):
        create_credit_note = values.get("create_credit_note", False)
        if create_credit_note:
            values["type"] = "in_refund"
        return super().create(values)

    def write(self, values):
        is_customer_invoice = values.get("is_customer_invoice", False)
        if not is_customer_invoice:
            return super().write(values)
        for invoice in self:
            if not (invoice.partner_id.fiscalcode or invoice.partner_id.vat):
                raise UserError("Define VAT or Fiscalcode for customer {name}".format(name=self.partner_id.name))
        return super().write(values)

    @api.depends("is_customer_invoice")
    def _get_customer_number_identifier(self):
        for invoice in self:
            invoice.customer_number_identifier = ".1" if invoice.is_customer_invoice else ""

    def action_move_create(self):
        res = super().action_move_create()
        for invoice in self:
            if invoice.is_customer_invoice and not invoice.move_name.endswith(".1"):
                complete_number = "{number}.1".format(number=invoice.move_name)
                invoice.move_name = complete_number
                invoice.move_id.name = complete_number
            elif not invoice.is_customer_invoice and invoice.move_name.endswith(".1"):
                complete_number = invoice.move_name[:-2]
                invoice.move_name = complete_number
                invoice.move_id.name = complete_number
        return res


class AccountInvoiceLine(models.Model):

    _inherit = "account.move.line"

    invoice_date = fields.Date(string="Invoice Date", related="move_id.invoice_date", store=True)

    price_compute_tax = fields.Float(
        string="Price Total", store=True, compute="_compute_tax_price", digits="Product Price"
    )

    tax_value = fields.Float(string="VAT Amount", store=True, compute="_compute_tax_price", digits="Product Price")

    @api.depends("product_id", "price_unit", "tax_ids", "quantity")
    def _compute_tax_price(self):
        for line in self:
            result = line.tax_ids.compute_all(line.price_unit * line.quantity)
            line.tax_value = result["total_included"] - result["total_excluded"]
            line.price_compute_tax = result["total_included"]


class AccountPaymentCashOnDelivery(models.TransientModel):
    _name = "netaddiction.account.payment.cod"

    cod_file = fields.Binary(string="Carica il file (*.csv)", attachment=False)
    # results
    return_text = fields.Text("Messaggio di ritorno")
    order_not_found = fields.Text("Ordini non trovati")
    payment_not_found = fields.Text("Pagamenti non trovati")
    generic_error = fields.Text("Errori generici")

    def check_csv_cod(self):
        if self.cod_file:
            csv_data = base64.b64decode(self.cod_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            reader = csv.DictReader(data_file, delimiter=";")

            head = next(reader)
            head = {k.strip(): v for (k, v) in head.items()}
            is_brt = True if HEAD_BRT in head else False
            key = HEAD_BRT if is_brt else HEAD_SDA
            money_key = MONEY_BRT if MONEY_BRT in head else MONEY_SDA

            warning_list = {"order_not_found": [], "payment_not_found": [], "error": []}
            cod_journal = self.env["ir.model.data"].get_object("netaddiction_payments", "contrassegno_journal")

            try:
                self._check_line(head, key, money_key, is_brt, cod_journal.id, warning_list)
            except Exception as e:
                warning_list["error"].append(f"Problema con {head} | Motivazione: {e}")

            for line in reader:
                try:
                    line = {k.strip(): v for (k, v) in line.items()}
                    self._check_line(line, key, money_key, is_brt, cod_journal.id, warning_list)
                except Exception as e:
                    warning_list["error"].append(f"Problema con {line} | Motivazione: {e}")

            if warning_list:
                self.return_text = "Non sono stati trovati pagamenti in contrassegno per i seguenti ordini"
                self.order_not_found = "<br/>".join(map(str, warning_list["order_not_found"]))
                self.payment_not_found = "<br/>".join(map(str, warning_list["payment_not_found"]))
                self.generic_error = "<br/>".join(map(str, warning_list["error"]))
            else:
                self.return_text = "Registrazione avvenuta con successo!"

    def _check_line(self, line, key, money_key, is_brt, cod_id, warning_list):
        found = False
        if line[key] and line[money_key]:
            order = None
            if is_brt:
                order = self.env["sale.order"].search([("id", "=", line[key])])
            else:
                pick = self.env["stock.picking"].search([("id", "=", line[key])])
                order = pick.sale_id if pick else None
            if order:
                amount_str = line[money_key].replace(",", ".").replace("€", "")
                amount = float(amount_str)

                for tx in order.transaction_ids:
                    if (
                        (abs(order.amount_total - amount) <= 0.009)
                        and tx.acquirer_id.journal_id.id == cod_id
                        and tx.state != "posted"
                    ):
                        tx._set_transaction_done()
                        found = True
                        break
                if not found:
                    warning_list["payment_not_found"].append(
                        f"Ordine: <b>{order.name}</b> | ID: <b>{line[key]}</b> | Importo: <b>{amount_str} €</b>"
                    )
                else:
                    all_paid = True
                    for p in order.transaction_ids:
                        all_paid = all_paid and p.state == "posted"
                    if all_paid:
                        order.date_done = fields.Datetime.now()
            else:
                warning_list["order_not_found"].append(f"ID: <b>{line[key]}</b>")
