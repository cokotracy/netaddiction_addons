# -*- coding: utf-8 -*-
from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class Gedistribuzione(supplier.Supplier):

    files = [
        {
            'name': 'Main',
            'mapping': (
                ('multiplayer.csv', (
                    'barcode',
                    'codice_fornitore',
                    'prezzo_acquisto',
                    'qty',
                    'nome',
                    'descrizione',
                    'prezzo_suggerito',
                    'immagine',
                    'data_uscita',
                    'categoria',
                    'tassa_acquisto',
                    'tassa_vendita',
                )),
            ),
        },
    ]

    downloader = FTPDownloader(
        hostname='ftp.gedistribuzione.com',
        username='multiplayer',
        password='Mxt8b02@')

    parser = CSVParser(
        skip_first=True,
        delimiter=',')

    mapping = Adapter(
        barcode='barcode',
        name='nome',
        description='descrizione',
        price='prezzo_suggerito',
        supplier_code='codice_fornitore',
        supplier_price='prezzo_acquisto',
        supplier_quantity='qty')

    categories = 'tassa_vendita', 'categoria'

    def validate(self, item):
        import datetime
        assert item['qty'] > 0
        assert item['prezzo_suggerito'] > 0
        assert item['data_uscita'] >= datetime.date(2015, 1, 1).strftime('%d/%m/%Y')

    def group(self, item):
        return None
