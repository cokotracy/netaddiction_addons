import csv
import io
import base64

from odoo import fields, models

HEAD_SDA = "Numero riferimento spedizione"
HEAD_BRT = "Riferimenti"
MONEY_SDA = "Importo contrassegno"
MONEY_BRT = "Euro"


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
