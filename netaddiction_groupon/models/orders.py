# -*- coding: utf-8 -*-
from openerp import models, fields

class GrouponOrder(models.Model):

    _name = "groupon.sale.order"

    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('sent', 'Completato'),
    ], string='Stato', readonly=True, copy=False, index=True)

    groupon_number = fields.Char(string="Numero Ordine Groupon")

    groupon_order_date = fields.Datetime(string="Data ordine su groupon")

    customer_comment = fields.Text(string="Commento Cliente")

    product = fields.many2one('product.product', 'Prodotto')

    quantity = field.Integer(string="Quantità")

    partner_shipping_id = fields.many2one('res.patner', 'Indirizzo spedizione')

    partner_invoice_id = fields.many2one('res.patner', 'Indirizzo fatturazione')

    groupon_cost = fields.Float(string="Prezzo di acquisto Groupon")

    groupon_sell_price = fields.Float(string="Prezzo di vendita Groupon")


    def create_addresses(self):
    		return 1
			# creare user e indirizzo che sega
            company_id = self.env["res.company"].search([("name", "=", "Multiplayer.com")])[0].id
            user = self.env["res.partner"].create({
                'name': shipping_dict["name"],
                'company_id': company_id,
                'email': buyer["Email"],
                'is_company': True,
                'customer': True,
                'type': 'contact',
                'phone': shipping_dict["phone"],
                'notify_email': 'none'})
            user_shipping = self.env["res.partner"].create({
                'name': shipping_dict["name"],
                'company_id': company_id,
                'street': shipping_dict["street"],
                'street2': shipping_dict["street2"],
                'phone': shipping_dict["phone"],
                'country_id': italy_id.id,
                'city': shipping_dict["city"],
                'zip': shipping_dict["zip"],
                'parent_id': user.id,
                'is_company': False,
                'customer': True,
                'type': 'delivery',
                'notify_email': 'none'})
            user_billing = self.env["res.partner"].create({
                'name': shipping_dict["name"],
                'company_id': company_id,
                'street': shipping_dict["street"],
                'street2': shipping_dict["street2"],
                'phone': shipping_dict["phone"],
                'country_id': italy_id.id,
                'city': shipping_dict["city"],
                'zip': shipping_dict["zip"],
                'parent_id': user.id,
                'is_company': False,
                'customer': True,
                'type': 'invoice',
                'notify_email': 'none'})