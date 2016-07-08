# -*- coding: utf-8 -*-

from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import RegexParser


VAT = 22
DISCOUNT = 35


class CosmicGroup(supplier.Supplier):
    files = [
        {
            'name': 'Main',
            'mapping': {
                'magazzino/a6sinte.txt': (
                    'editore',
                    'codice',
                    'titolo',
                    'prezzo',
                    'quantita',
                ),
            },
        },
    ]

    downloader = FTPDownloader(
        hostname='ftp.cosmicgroup.eu',
        username='multiplayer',
        password='FYaHPbvExw')

    parser = RegexParser(
        pattern=r'\s*(.{0,16}[^\s])\s*;'
                r'\s*(.{0,8}[^\s])\s*;'
                r'\s*(.{0,40}[^\s])\s*;'
                r'\s*(.{0,7}[^\s])\s*;'
                r'\s*(.{0,4}[^\s])\s*;')

    mapping = Adapter(
        name='titolo',
        supplier_code='codice',
        supplier_price=lambda self, item: float(item['prezzo'].strip()) / (1 + VAT / 100) * (1 - DISCOUNT / 100),
        supplier_quantity='quantita')

    def validate(self, item):
        assert item['titolo'][0] != u'ø'
