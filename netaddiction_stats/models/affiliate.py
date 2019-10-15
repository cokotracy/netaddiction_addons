# -*- coding: utf-8 -*-

from openerp import models, api, fields
import datetime
from dateutil.relativedelta import *
import StringIO
import base64
import csv

class OrdersStats(models.Model):
    _inherit = "netaddiction.partner.affiliate"

    stats_last_month = fields.Binary(string="Mese Scorso", attachment=True)
    stats_last_month_filename = fields.Char("Mese Scorso Filename")

    @api.one
    def get_month_stats(self):
        one_month_ago = datetime.datetime.now() - relativedelta(months=1)
        date_start = one_month_ago.replace(day=1, hour=00, minute=00, second=00)
        self.stats_last_month_filename = '%s_%s.csv' % (self.partner_id.name.replace(' ', '_'), date_start.strftime("%B_%Y"))
        date_start = datetime.datetime.strftime(date_start, '%Y-%m-%d %H:%M:%S')
        date_end = datetime.datetime.now().replace(day=1, hour=00, minute=00, second=00)
        date_end = datetime.datetime.strftime(date_end, '%Y-%m-%d %H:%M:%S')

        orders = self.env['netaddiction.partner.affiliate.order.history'].search([('affiliate_id', '=', self.id), ('order_date_done', '>=', date_start), ('order_date_done', '<', date_end)])

        month_file = StringIO.StringIO()
        month_file_csv = csv.writer(month_file)
        data = ['ORDINE', 'DATA ORDINE', 'DATA SPEDIZIONE', 'PRODOTTO', 'QUANTITA', 'PREZZO VENDITA', 'COSTO', 'MARGINE', 'PREZZO VENDITA IVATO', 'COSTO IVATO']
        month_file_csv.writerow(data)
        data = []
        month_file_csv.writerow(data)
        price_total = 0
        cost_total = 0
        margin_total = 0
        price_total_tax = 0
        cost_total_tax = 0
        for order in orders:
            margin = order.order_id.get_margin()
            del(margin['total'])
            for pick in margin:
                for product in margin[pick]['products']:
                    values = margin[pick]['products'][product]
                    price_tax = values['sell_price'] + (values['sell_price'] * (product.taxes_id.amount / 100))
                    price_total_tax += price_tax

                    price_tax = "%.2f" % price_tax
                    cost_tax = values['cost'] + (values['cost'] * (product.supplier_taxes_id.amount / 100))
                    cost_total_tax += cost_tax
                    cost_tax = "%.2f" % cost_tax

                    data = [order.order_id.name, order.order_id.date_order, order.order_date_done, product.display_name, values['qty'], values['sell_price'], values['cost'], values['margin'], price_tax, cost_tax]
                    month_file_csv.writerow(data)
                    price_total += values['sell_price']
                    cost_total += values['cost']
                    margin_total += values['margin']

        data = []
        month_file_csv.writerow(data)
        data = ['', '', '', '', '', "%.2f" % price_total, "%.2f" % cost_total, "%.2f" % margin_total, "%.2f" % price_total_tax, "%.2f" % cost_total_tax]
        month_file_csv.writerow(data)

        self.stats_last_month = base64.b64encode(month_file.getvalue().encode("utf8"))
