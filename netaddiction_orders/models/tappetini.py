# -*- coding: utf-8 -*-
import base64
import io
import csv
import re
import random
from openerp import models, fields, api
from openerp.exceptions import ValidationError

filter_nonascii = lambda s: re.sub(r'[^\x00-\x7F]+',' ', s)

class TappetiniImporter(models.TransientModel):
    _name = "netaddiction.tappetini.register"

    csv_file = fields.Binary('File')
    prod_id = fields.Integer('ID Prodotto')
    return_text = fields.Text("Messaggio di ritorno")

    @api.multi
    def execute(self):
        """Legge il csv e crea gli utenti di shopify."""
        self.ensure_one()
        if self.csv_file and self.prod_id and self.prod_id > 0:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.DictReader(decodedIO, delimiter=',')
            warning_list = []
            counter = 0
            total_rows = 0
            italy_id = self.env["res.country"].search([('code', '=', 'IT')])[0].id
            for line in reader:
                total_rows += 1
                try:
                    self.create_addresses_and_order(line, italy_id,) 
                    counter += 1
                except ValidationError as e:
                    return 1
                except Exception as e:
                    warning_list.append((e, line['E-MAIL']))
            if warning_list:
                self.return_text = "PROBLEMA: IMPORTATI SOLO %s su %s /n ATTENZIONE PROBLEMI CON QUESTI ORDINI: %s" % (counter, total_rows, warning_list)
            else:
                self.return_text = "ok importati %s su %s" % (counter, total_rows)

    def create_addresses_and_order(self, line, italy_id):

        user = self.env["res.partner"].search([("email", "=", line["E-MAIL"])])
        user = user[0] if user else None
        name = filter_nonascii(line["NOME"]) + " " + filter_nonascii(line["COGNOME"])
        phone = line['CELLULARE']
        company_id = self.env.user.company_id.id
        if not user:
            user = self.env["res.partner"].create({
                'name': name,
                'company_id': company_id,
                'email': line['E-MAIL'],
                'is_company': False,
                'customer': True,
                'company_type': 'person',
                'type': 'contact',
                'phone': phone,
                'notify_email': 'none',
            })

        country_state = self.env["res.country.state"].search([("code", "=", line["PROVINCIA"])])
        prov = country_state.id if len(country_state) == 1 else None
        country_id = italy_id
        # creare user e indirizzo che sega
        street = filter_nonascii(line["INDIRIZZO COMPLETO"])
        street2 = "SNC"
        parsed = re.findall('\d+', filter_nonascii(line["INDIRIZZO COMPLETO"]))
        if parsed:
            street2 = parsed[-1]
            street = re.sub(parsed[-1], '', street)

        user_shipping = self.env["res.partner"].create({
            'name': name,
            'company_id': company_id,
            'street': street,
            'street2': street2,
            'phone': phone,
            'country_id': country_id,
            'city': filter_nonascii(line["LOCALITA"]),
            'zip': line["CAP"].zfill(5),
            'state_id': prov,
            'parent_id': user.id,
            'is_company': False,
            'customer': True,
            'type': 'delivery',
            'notify_email': 'none',
            'is_default_address': True})
        user_billing = self.env["res.partner"].create({
            'name': name,
            'company_id': company_id,
            'street': street,
            'street2': street2,
            'phone': phone,
            'country_id': country_id,
            'city': filter_nonascii(line["LOCALITA"]),
            'zip': line["CAP"].zfill(5),
            'state_id': prov,
            'parent_id': user.id,
            'is_company': False,
            'customer': True,
            'type': 'invoice',
            'notify_email': 'none'})

        # creare ordine e mandarlo in lavorazione
        # public_price_list = self.env["product.pricelist"].search([("name", "=", "Listino Pubblico")])[0].id
        sda = self.env["delivery.carrier"].search([('name', '=', 'Corriere Espresso SDA')])[0].id
        brt = self.env["delivery.carrier"].search([('name', '=', 'Corriere Espresso BRT')])[0].id
        # print public_price_list
        journal_id = None

        pay_pal_tran_id = 'PRONTOCAMPAIGN'
        if (line["Tipo di pagamento"] == "Contrassegno"):
            journal_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal').id
        else:
            journal_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal').id

        order = self.env["sale.order"].create({
            'partner_id': user.id,
            'partner_invoice_id': user_billing.id,
            'partner_shipping_id': user_shipping.id,
            'state': 'draft',
            'delivery_option': 'all',
            'carrier_id': random.choice([sda, brt]),
            'payment_method_id': journal_id,
            'pay_pal_tran_id': pay_pal_tran_id,
            'pronto_campaign': True,
        })
        # print transaction["TransactionPrice"]
        quantity = int(line["Quanti"])
        prod = self.env["product.product"].browse(self.prod_id)
        if not prod:
            return "product not found %s " % prod
        price = float(line["Amount"].replace(',', '.')) / quantity
        print float(line["Amount"].replace(',', '.'))
        print price

        order_line = self.env["sale.order.line"].create({
            "order_id": order.id,
            "product_id": prod.id,
            "product_uom_qty": quantity,
            "product_uom": prod.uom_id.id,
            "name": prod.display_name,
            "price_unit": float(price),
        })

        order.extract_cart_offers()
        order.action_confirm()

        if (line["Tipo di pagamento"] == "Contrassegno"):
            transient = self.env["netaddiction.cod.register"].create({})
            transient.set_order_cash_on_delivery_at_price(order.id)
        else:
            transient = self.env["netaddiction.paypal.executor"].create({})
            transient._register_payment(order.partner_id.id, order.amount_total, order.id, order.pay_pal_tran_id)

        return 1