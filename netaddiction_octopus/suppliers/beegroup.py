# -*- coding: utf-8 -*-
from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class CustomSupplier(supplier.Supplier):

    files = [
        {
            'name': 'Main',
            'mapping': (
                ('stock.csv', (
                    'Cod.',
                    'Descrizione',
                    'Tipologia',
                    'Categoria',
                    'U.m.',
                    'Iva',
                    'Listino 2',
                    'Note',
                    'Cod. a barre',
                    'Produttore',
                    'E-commerce',
                    'Vendita Touch',
                    'MATERIALE',
                    'PACKAGING',
                    'PEZZI NEL CASE',
                    'SCAD. PRE',
                    'Cod per il F.',
                    'Fornitore',
                    'Note fornitura',
                    'Ordina multipli di',
                    'Gg. ordine',
                    'Scorta min.',
                    'Ubicazione',
                    'Q.t\xc3\xa0 disponibile',
                    'Stato magazz.',
                    'U.m. Dim.',
                    'Vol. netto',
                    'Vol. imballo',
                )),
            ),
        },
    ]

    downloader = FTPDownloader(
        hostname='srv-ftp.multiplayer.com',
        username='ecom-00002',
        password='cfnr89nf98nf84')

    parser = CSVParser(
        skip_first=True,
        delimiter=';')

    mapping = Adapter(
        barcode='Cod. a barre',
        name='Descrizione',
        description='Note',
        supplier_code='Cod.',
        supplier_price=lambda self, item:
        float(item['Listino 2'].replace(',', '.')),
        supplier_quantity='Q.t\xc3\xa0 disponibile')

    categories = 'Iva', 'Tipologia'

    def group(self, item):
        return None
