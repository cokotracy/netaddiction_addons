# -*- coding: utf-8 -*-

import csv

from ftplib import FTP
from io import BytesIO

from openerp import api, models


class Cron(models.Model):
    _name = 'netaddiction_warehouse.inventory_csv_builder'

    FTP_HOST = 'srv-ftp.multiplayer.com'
    FTP_USER = 'test-mcom'
    FTP_PASS = '65-hy.mn'

    @api.model
    def run(self):
        category_model = self.env['product.category']
        product_model = self.env['product.product']
        pricelist_model = self.env['product.pricelist']

        pricelist = pricelist_model.browse(15)  # TODO estrarre

        categories = category_model.search([])
        csv_files = {}

        for category in categories:
            products = product_model.search([('categ_id', '=', category.id), ('qty_available_now', '>', 0)])

            csv_buffer = BytesIO()
            csv_writer = csv.writer(csv_buffer)
            csv_name = '%s.csv' % category.name.replace(' ', '-').lower()

            csv_writer.writerow((
                'ID',
                'Barcode',
                'Prodotto',
                'Quantità',
                'Prezzo',
            ))

            for product in products:
                price = pricelist.price_get(product.id, 1)[pricelist.id]
                price = round(product.taxes_id.compute_all(price)['total_excluded'], 2)

                row = (
                    product.id,
                    product.barcode,
                    unicode(product.name).encode('utf-8'),
                    product.qty_available_now,
                    price,
                )

                csv_writer.writerow(row)

            csv_buffer.seek(0)

            csv_files[csv_name] = csv_buffer

        # Upload

        ftp = FTP(self.FTP_HOST, self.FTP_USER, self.FTP_PASS)

        for csv_name, csv_buffer in csv_files.items():
            ftp.storbinary('STOR %s' % csv_name, csv_buffer)

        ftp.quit()
