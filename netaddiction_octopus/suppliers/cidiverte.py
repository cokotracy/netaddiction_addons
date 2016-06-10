from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class Cidiverte(supplier.Supplier):
    files = [
        {
            'name': 'Main',
            'mapping': {
                'listino_multiplayer.txt': (
                    'barcode',
                    'codice',
                    'prezzo',
                    'disponibilita',
                )
            }
        },
    ]

    downloader = FTPDownloader(
        hostname='srv-ftp.multiplayer.com',
        username='shop-cidiverte',
        password='12.cx-9g')

    parser = CSVParser(
        skip_first=True,
        delimiter='|',
        linebreak='\n')

    mapping = Adapter(
        barcode='barcode',
        supplier_code='codice',
        supplier_quantity=lambda self, item: 50 if item['disponibilita'] == 'SI' else 0)
