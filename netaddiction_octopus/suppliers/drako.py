from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class Drako(supplier.Supplier):
    files = [
        {
            'name': 'Main',
            'mapping': {
                'multiplayer_it.txt': (
                    'Nome_Cat',
                    'ID_Articolo',
                    'Codice_Vendor',
                    'Nome',
                    'Descrizione',
                    'Peso',
                    'Prezzo_listino',
                    'Prezzo_promo',
                    'Prezzo',
                    'Produttore',
                    'IVA',
                    'Dispo',
                    'Dispo_Fut',
                    'Data_Dispo',
                    'EAN',
                    'Indirizzo Immagine',
                    'Testo Prodotto',
                ),
            },
        },
    ]

    downloader = FTPDownloader(
        hostname='ftp.drako.it',
        username='Multiplayer_it',
        password='ErNE4IWX')

    parser = CSVParser(
        delimiter='\t',
        linebreak='\n',
        skip_first=True)

    mapping = Adapter(
        barcode='EAN',
        name='Nome',
        description=lambda self, item: '<br><br>'.join([item['Descrizione'], item['Testo Prodotto']]) if item['Descrizione'] and item['Testo Prodotto'] else item['Testo Prodotto'],
        image='Indirizzo Immagine',
        date=lambda self, item: item['Data_Dispo'] or None,
        supplier_code='Codice_Vendor',
        supplier_price=lambda self, item: float(item['Prezzo'].replace(',', '.')) if item['Prezzo'] else None,
        supplier_quantity='Dispo')
