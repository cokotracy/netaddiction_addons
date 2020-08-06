from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class CustomSupplier(supplier.Supplier):
    files = [
        {
            'name': 'Main',
            'mapping': (
                ('listino_prvd.txt', (
                    'barcode',
                    'codice',
                    'descrizione',
                    'codice_piattaforma',
                    'piattaforma',
                    'codice_gruppo',
                    'gruppo',
                    'codice_sottogruppo',
                    'sottogruppo',
                    'prevendita',
                    'novita',
                    'day_one',
                    'prezzo_acquisto',
                    'prezzo_pubblico',
                    'disponibile',
                    'filtro',
                    'codice_marca',
                    'marca',
                    'data_modifica_acquisto',
                    'data_modifica_vendita',
                    'data_modifica_articolo',
                    'sku',
                )),
            ),
        },
    ]

    downloader = FTPDownloader(
        hostname='ftp.opengames.it',
        username='37102',
        password='ftp_37102!')

    parser = CSVParser(
        delimiter='|',
        linebreak='\n')

    mapping = Adapter(
        barcode='barcode',
        supplier_code='codice',
        supplier_quantity=lambda self, item: 50 if item['disponibile'] == 'S' else 0,
        supplier_price=lambda self, item: item['prezzo_acquisto'].replace(',', '.'),
        name='descrizione')
