# -*- coding: utf-8 -*-
import base64
import io
import csv
import re
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
import datetime


class GrouponOrder(models.Model):

    _name = "netaddiction.groupon.sale.order"

    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('sent', 'Completato'),
    ], string='Stato', readonly=True, copy=False, index=True, default="draft")

    name = fields.Char(string="nome", compute="_get_order_name")

    groupon_number = fields.Char(string="Numero Ordine Groupon", required=True)

    groupon_order_date = fields.Datetime(string="Data ordine su groupon")

    product_id = fields.Many2one('product.product', 'Prodotto')

    quantity = fields.Integer(string="Quantità")

    partner_shipping_id = fields.Many2one('res.partner', 'Indirizzo spedizione')

    partner_invoice_id = fields.Many2one('res.partner', 'Indirizzo fatturazione')

    groupon_cost = fields.Float(string="Prezzo di acquisto Groupon")

    groupon_sell_price = fields.Float(string="Prezzo di vendita Groupon")

    picking_ids = fields.Many2many('stock.picking', string='Spedizioni')

    wave_id = fields.Many2one(comodel_name="groupon.pickup.wave", string="Lista Prelievo")

    @api.one
    def _get_order_name(self):
        self.name = 'GRP%05d' % (self.id)

    @api.one
    @api.constrains('groupon_number')
    def _check_groupon_number(self):
        if len(self.search([('groupon_number', '=', self.groupon_number)])) > 1:
                raise ValidationError("Esiste già un ordine groupon con questo numero ordine %s" % self.groupon_number)

    @api.one
    def unlink(self):
        """Cancello solo gli ordini in draft."""
        # TODO: sistemare le picking: annullarle e valutare uno stato cancel
        if self.state == "draft":
            for pick in self.picking_ids:
                pick.unlink()
            super(GrouponOrder, self).unlink()

    @api.multi
    def create_shipping(self):
        # TODO: contorllare quantità e semmai mettere in problema
        groupon_shipping_type = self.env.ref('netaddiction_groupon.groupon_customer_type_out').id
        groupon_warehouse = self.env.ref('netaddiction_groupon.netaddiction_stock_groupon').id
        customer_wh = self.env.ref('stock.stock_location_customers').id
        for order in self:
            if len(order.picking_ids) == 0:
                # creare la spedizione
                attr = {
                    'picking_type_id': groupon_shipping_type,
                    'move_type': 'one',
                    'priority': '1',
                    'location_id': groupon_warehouse,
                    'location_dest_id': customer_wh,
                    'partner_id': order.partner_shipping_id.id,
                    'move_lines': [(0, 0, {'product_id': order.product_id.id, 'product_uom_qty': int(order.quantity),
                        'state': 'draft',
                        'product_uom': order.product_id.uom_id.id,
                        'name': 'Magazzino Groupon > Punto di Stoccaggio Partner/Clienti',
                        'picking_type_id': groupon_shipping_type,
                        'origin': '%s' % (order.name,)})],
                }
                pick = self.env['stock.picking'].sudo().create(attr)
                pick.sudo().action_confirm()
                pick.sudo().force_assign()
                order.picking_ids = [(4, pick.id, False)]
        return True

class GrouponRegister(models.TransientModel):
    _name = "netaddiction.groupon.register"

    csv_file = fields.Binary('File')

    @api.multi
    def execute(self):
        """Legge il csv e crea gli ordini di groupon."""
        self.ensure_one()
        if self.csv_file:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.DictReader(decodedIO, delimiter=',')
            groupon_user_id = self.env['ir.values'].search([("name", "=", "groupon_customer_id"), ("model", "=", "groupon.config")]).value
            warning_list = []
            counter = 0
            total_rows = 0
            for line in reader:
                total_rows += 1
                try:
                    self.create_addresses_and_order(groupon_user_id, line)
                    counter += 1
                except Exception as e:
                    warning_list.append((e, line['groupon_number']))

            if warning_list:
                raise Warning("PROBLEMA: IMPORTATI SOLO %s su %s" % (counter, total_rows), "ATTENZIONE PROBLEMI CON QUESTI ORDINI: %s" % warning_list)
            else:
                raise Warning("TUTTO OK caricati %s ordini" % counter)


    def create_addresses_and_order(self, groupon_user_id, line):
        # creare user e indirizzo che sega
        italy_id = self.env["res.country"].search([('code', '=', 'IT')])[0]
        ship_address_street, ship_address_number = self.split_addresses(line["shipment_address_street"], line["shipment_address_street_2"])
        bill_address_street, bill_address_number = self.split_addresses(line["billing_address_street"], '')

        company_id = self.env.user.company_id.id
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
        product = self.env["product.product"].search([("barcode", "=", line["merchant_sku_item"])])
        if not product:
            raise Exception("Prodotto %s" % line["merchant_sku_item"])
        order = self.env["netaddiction.groupon.sale.order"].create({
            'partner_invoice_id': user_billing.id,
            'partner_shipping_id': user_shipping.id,
            'state': 'draft',
            'groupon_number': line['groupon_number'],
            'groupon_order_date': line['order_date'],
            'quantity': line['quantity_requested'],
            'groupon_cost': line["groupon_cost"],
            'groupon_sell_price': line["sell_price"],
            'product_id': product.id})

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