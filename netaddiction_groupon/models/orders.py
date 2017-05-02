# -*- coding: utf-8 -*-
import base64
import io
import csv
import re
from openerp import models, fields, api


class GrouponOrder(models.Model):

    _name = "netaddiction.groupon.sale.order"

    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('sent', 'Completato'),
    ], string='Stato', readonly=True, copy=False, index=True)

    groupon_number = fields.Char(string="Numero Ordine Groupon")

    groupon_order_date = fields.Datetime(string="Data ordine su groupon")

    customer_comment = fields.Text(string="Commento Cliente")

    product_id = fields.Many2one('product.product', 'Prodotto')

    quantity = fields.Integer(string="Quantità")

    partner_shipping_id = fields.Many2one('res.patner', 'Indirizzo spedizione')

    partner_invoice_id = fields.Many2one('res.patner', 'Indirizzo fatturazione')

    groupon_cost = fields.Float(string="Prezzo di acquisto Groupon")

    groupon_sell_price = fields.Float(string="Prezzo di vendita Groupon")

    picking_ids = fields.Many2many('stock.picking', string='Spedizioni')


class GrouponRegister(models.TransientModel):
    _name = "netaddiction.groupon.register"

    csv_file = fields.Binary('File')
    return_text = fields.Text("Messaggio di ritorno")

    @api.multi
    def execute(self):
        """Legge il csv e crea gli ordini di groupon."""
        if self.csv_file:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.DictReader(decodedIO, delimiter=',')
            groupon_user_id = self.env['ir.values'].search([("name", "=", "groupon_customer_id"), ("model", "=", "groupon.config")]).value

            for line in reader:
                print line

            return 1

            if warning_list:
                self.return_text = "non sono stati trovati pagamenti in contrassegno per i seguenti ordini nel file: %s" % warning_list
            else:
                self.return_text = "tutto ok!"

    def create_addresses_and_order(self, groupon_user_id, line):
        return 1
        # creare user e indirizzo che sega
        italy_id = self.env["res.country"].search([('code', '=', 'IT')])[0]
        ship_address_street, ship_address_number = self.split_addresses(line["shipment_address_street"], line["shipment_address_street_2"])
        bill_address_street, bill_address_number = self.split_addresses(line["billing_address_street"], '')

        company_id = self.env["res.company"].search([("name", "=", "Multiplayer.com")])[0].id
        user_shipping = self.env["res.partner"].create({
            'name': line["shipment_address_name"],
            'company_id': company_id,
            'street': ship_address_street,
            'street2': ship_address_number,
            'phone': line["customer_phone"],
            'country_id': italy_id.id,
            'city': line["shipment_address_city"],
            'zip': line["shipment_address_postal_code"],
            'parent_id': groupon_user_id,
            'is_company': False,
            'customer': True,
            'type': 'delivery',
            'notify_email': 'none'})
        user_billing = self.env["res.partner"].create({
            'name': line["billing_address_name"],
            'company_id': company_id,
            'street': bill_address_street,
            'street2': bill_address_number,
            'phone': line["customer_phone"],
            'country_id': italy_id.id,
            'city': line["billing_address_city"],
            'zip': line["billing_address_postal_code"],
            'parent_id': groupon_user_id,
            'is_company': False,
            'customer': True,
            'type': 'invoice',
            'notify_email': 'none'})
        order = self.env["netaddiction.groupon.sale.order"].create({
            'partner_invoice_id': user_billing.id,
            'partner_shipping_id': user_shipping.id,
            'state': 'draft',
            'groupon_number': line[''],
            'groupon_order_date': line[''],
            'customer_comment': line['']})

    def split_addresses(self, street1, street2):
        address_number = street2
        address_street = street1
        if not address_number:
            parsed = re.findall('\d+', address_street)
            if parsed:
                address_number = parsed[-1]
                # shipping_dict["street"].translate(None, parsed[-1])
                address_street = re.sub(parsed[-1], '', address_street)
        return address_street, address_number

