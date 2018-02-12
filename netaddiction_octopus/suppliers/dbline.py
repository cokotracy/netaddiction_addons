import re

from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class DbLine(supplier.Supplier):
    files = [
        {
            'name': 'Main',
            'mapping': (
                ('/NSArea/A17/ECOPRO.TXT', (
                    'categoria',
                    'prenotazione',
                    'data_uscita',
                    'codice_fornitore',
                    'barcode',
                    'titolo',
                    'descrizione_breve',
                    'descrizione',
                    'requisiti',
                    'disponibile',
                    'quantita',
                    'costo',
                    'iva',
                    'prezzo',
                    'prezzo_bis',
                    'codice_genere',
                    'codice_publisher',
                    'valutazione',
                    'data_inserimento',
                    'prezzo_vendita_dbline',
                )),
            ),
        },
    ]

    categories = 'categoria', 'iva'

    downloader = FTPDownloader(
        hostname='ftp.dbline.it',
        username='area17',
        password='multi.17')

    parser = CSVParser(
        enclosure='|')

    mapping = Adapter(
        barcode='barcode',
        name='titolo',
        description='descrizione',
        price='prezzo_bis',
        date=lambda self, item: '20' + '-'.join(reversed(item['data_uscita'].split('/'))) if re.match(r'^\d{2}/\d{2}/\d{2}$', item['data_uscita']) else None,
        supplier_code='codice_fornitore',
        supplier_price='costo',
        supplier_quantity='quantita')

    def validate(self, item):
        categories = (
            'GAAA',
            'GACC',
            'ACCE',
            'PS4',
            'PSVR',
            'XONE',
            'SWI',
            'CDGI',
            'CAR',
            'COS',
            'GTA',
            'FIG',
            'ARG',
            'DVD',
            'BRY',
        )

        assert len([category for category in categories if item['codice_fornitore'].startswith(category)]) > 0

    def group(self, item):
        return None
