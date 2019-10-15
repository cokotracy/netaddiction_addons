# -*- coding: utf-8 -*-

from openerp import models, api, fields
import base64
import datetime
import io
import csv

class ReconciliationOrders(models.TransientModel):
    _name = "netaddiction.reconciliation.orders"

    date_start = fields.Date(string="Data Inizio")
    date_finish = fields.Date(string="Data Fine")
    file = fields.Binary(string="Carica File Csv")
    file_download = fields.Binary(string="Scarica File Csv")
    method = fields.Selection(string="Tipo", selection=[('paypal', 'PayPal'), ('cc', 'Carta di Credito')])

    payment_verified = fields.Many2many(string="Pagamenti Verificati", comodel_name="account.payment", relation="payment_verified")
    payment_verified_draft = fields.Many2many(string="Pagamenti Verificati Bozza", comodel_name="account.payment", relation="payment_verified_draft")
    payment_verified_not_amount = fields.Many2many(string="Pagamenti Verificati Prezzo diverso", comodel_name="account.payment", relation="payment_verified_not_amount")
    payment_not_verified = fields.Many2many(string="Pagamenti Non Verificati", comodel_name="account.payment", relation="payment_not_verified")

    extra = fields.Text(string="Extra")

    total_verified = fields.Float(string="Verificati", compute="_calculate_verified")
    total_not_verified = fields.Float(string="Non Verificati", compute="_calculate_verified")

    @api.one
    def verify(self):
        pp = self.env.ref('netaddiction_payments.paypal_journal').id
        cc = self.env.ref('netaddiction_payments.cc_journal').id
        first = datetime.datetime.strptime(self.date_start, '%Y-%m-%d')
        last = datetime.datetime.strptime(self.date_finish, '%Y-%m-%d')
        csv_file = base64.b64decode(self.file)
        csv_bytes = io.BytesIO(csv_file)
        spamreader = csv.reader(csv_bytes)

        output = io.BytesIO()
        writer = csv.writer(output)

        verified = []
        vdraft = []
        extra = '<div class="oe_list o_list_view oe_view"><table class="oe_list_content">'
        allpay = []
        payment_verified_not_amount = []
        if self.method == 'paypal':
            payments = self.env['account.payment'].search([('payment_date', '>=', datetime.datetime.strftime(first, '%Y-%m-%d 00:00:00')), ('payment_date', '<=', datetime.datetime.strftime(last, '%Y-%m-%d 23:59:59')),
                ('journal_id', '=', pp), ('payment_type', '=', 'inbound')])
            for line in spamreader:
                tranid = line[14]
                value = line[8]
                name = line[3]
                email = line[12]
                tip = line[4]
                what = line[44]
                date_paypal = line[0]
                new_value = [int(i) for i in value if i.isdigit()]
                decimal = new_value[-2:]
                number = new_value[:-2]
                n = ''
                for i in number:
                    n += str(i)
                d = ''
                for i in decimal:
                    d += str(i)
                val = n + '.' + d
                verify = False
                csvdata = False
                for payment in payments:
                    allpay.append(payment.id)
                    if payment.paypal_transaction_id:
                        if payment.paypal_transaction_id.strip() == tranid.strip():
                            verify = True
                            if payment.state == 'posted':
                                if float(round(payment.amount, 2)) == float(val):
                                    verified.append(payment.id)
                                else:
                                    payment_verified_not_amount.append(payment.id)
                                    csvdata = [payment.payment_date, payment.journal_id.name, payment.order_id.name, payment.partner_id.name, payment.amount, payment.state, payment.paypal_transaction_id, payment.cc_last_four]
                            else:
                                vdraft.append(payment.id)
                                csvdata = [payment.payment_date, payment.journal_id.name, payment.order_id.name, payment.partner_id.name, payment.amount, payment.state, payment.paypal_transaction_id, payment.cc_last_four]
                if not verify:
                    if tranid == 'Codice transazione':
                        extra += '<thead><tr class="oe_list_header_columns" style="font-weight: bolder;"><th><b>%s</b></th><th><b>%s</b></th><th><b>%s</b></th><th><b>%s</b></th><th><b>%s</b></th><th><b>%s</b></th></tr></thead>' % (tranid, name, email, value, tip, what)
                    else:
                        if what == 'Accredito':
                            extra += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (tranid, name, email, value, tip, what)
                            csvdata = [date_paypal, 'Paypal', '', name, value, '', tranid, '']
                if csvdata:
                    writer.writerow(csvdata)

        elif self.method == 'cc':
            payments = self.env['account.payment'].search([('payment_date', '>=', datetime.datetime.strftime(first, '%Y-%m-%d 00:00:00')), ('payment_date', '<=', datetime.datetime.strftime(last, '%Y-%m-%d 23:59:59')),
                ('journal_id', '=', cc), ('payment_type', '=', 'inbound')])
            for line in spamreader:
                order_id = line[15]
                value = line[8]
                lastfour = line[5]
                date_bnl = line[0]
                new_value = [int(i) for i in value if i.isdigit()]
                decimal = new_value[-2:]
                number = new_value[:-2]
                n = ''
                for i in number:
                    n += str(i)
                d = ''
                for i in decimal:
                    d += str(i)
                val = n + '.' + d
                verify = False
                csvdata = False
                for payment in payments:
                    allpay.append(payment.id)
                    if int(payment.order_id.id) == int(order_id):
                        if payment.state == 'posted':
                            verify = True
                            if float(round(payment.amount, 2)) == float(val):
                                verified.append(payment.id)
                            else:
                                payment_verified_not_amount.append(payment.id)
                                csvdata = [payment.payment_date, payment.journal_id.name, payment.order_id.name, payment.partner_id.name, payment.amount, payment.state, payment.paypal_transaction_id, payment.cc_last_four]
                        else:
                            vdraft.append(payment.id)
                            csvdata = [payment.payment_date, payment.journal_id.name, payment.order_id.name, payment.partner_id.name, payment.amount, payment.state, payment.paypal_transaction_id, payment.cc_last_four]
                if not verify:
                    extra += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (order_id, lastfour, value)
                    csvdata = [date_bnl, 'Carta di Credito', order_id, '', value, '', '', value]

                if csvdata:
                    writer.writerow(csvdata)

        extra += '</table></div>'
        not_verified = [i for i in allpay if i not in verified]
        self.payment_verified = [(6, False, verified)]
        self.payment_verified_draft = [(6, False, vdraft)]
        self.payment_verified_not_amount = [(6, False, payment_verified_not_amount)]
        self.payment_not_verified = [(6, False, not_verified)]
        self.extra = extra
        self.file_download = base64.b64encode(output.getvalue()).decode()
        output.close()

    @api.one
    def _calculate_verified(self):
        value = 0
        for payment in self.payment_verified:
            value += payment.amount
        for payment in self.payment_verified_draft:
            value += payment.amount
        for payment in self.payment_verified_not_amount:
            value += payment.amount

        self.total_verified = value

        not_value = 0
        for payment in self.payment_not_verified:
            not_value += payment.amount

        self.total_not_verified = not_value
