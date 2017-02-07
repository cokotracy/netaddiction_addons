import re

from datetime import datetime
from hashlib import md5

from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


DISCOUNTS = {
    'PVC Ingrosso': 25,
    'PVC Ingrosso N.S.': 20,
    'PVC Disney': 17.5,
    'PVC Distribuiti': 32,
    'PVC Distribuiti Editoriali': 32,
    'PVC Ingrosso Editoriali': 28,
    'PVC Ingrosso Dvd Edit': 25,
    'PVC Ingrosso N.S. Dvd Edit.': 20,
    'PVC Disney Edit.': 17.5,
    'PVC Distribuiti Dvd Edit': 32,
    'Editoriali - Distribuiti': 32,
    'Editoriali - Ingrosso': 28,
    'Abbigliamento': 40,
    'Toys Ing B - NR': 30,
    'Toys Dis B - NR': 32,
}


class TerminalVideo(supplier.Supplier):
    _MAPPING = {
        'catalog': (
            'Tipo record',
            '3D',
            'Anno di produzione (esteso)',
            'Anno produzione',
            'Area Dvd',
            'Cast',
            'Categoria sconto',
            'Cod. barre',
            'Cod. interno',
            'Codice',
            'Codice sottoformato',
            'Collana',
            'Colore',
            'Contenuti extra',
            'Data aggiornamento immagine',
            'Data fine offerta',
            'Data primo rilascio',
            'Data rilascio',
            'Distribuzione',
            'Durata',
            'Fascia eta',
            'Formato',
            'Formato audio',
            'Formato secondario',
            'Formato video',
            'Genere',
            'Genere principale',
            'Img Lrg Web',
            'Immagine',
            'Iva',
            'Lingue',
            'Listino',
            'Pvc',
            'Marca',
            'Nazione',
            'Numero supporti',
            'Offerta',
            'Premi',
            'Regia',
            'Sistema TV',
            'Sottotitoli',
            'Stato vendite',
            'Titolo',
            'Titolo originale',
            'Trama',
            'Vietato',
            'Taglia',
            'Genere T-Shirt',
            'Colore T-Shirt',
            CSVParser.EMPTY,
        ),
        'availability': (
            'Cod. barre',
            'Cod. interno',
            'Listino',
            'Pvc',
            'Q.ta in stock',
            'Categoria sconto',
            'Formato',
            'Iva',
            'Offerta',
            'Titolo',
            CSVParser.EMPTY,
        ),
    }

    files = [
        {
            'name': 'Merchandising',
            'mapping': {
                'Merchandising/DBmerchandisingFull.txt': _MAPPING['catalog'],
                'Stock/StocklistTotale.txt': _MAPPING['availability'],
            },
            'join': 'Cod. barre',
        },
        {
            'name': 'HomeVideo',
            'mapping': {
                'Video/DBHomeVideoFull.txt': _MAPPING['catalog'],
                'Stock/StocklistTotale.txt': _MAPPING['availability'],
            },
            'join': 'Cod. barre',
        },
        {
            'name': 'Libri',
            'mapping': {
                'Libri/DBLibriFull.txt': _MAPPING['catalog'],
                'Stock/StocklistTotale.txt': _MAPPING['availability'],
            },
            'join': 'Cod. barre',
        },
    ]

    categories = 'Formato', 'Genere principale', 'Taglia', 'Genere T-Shirt', 'Colore T-Shirt', 'Iva'

    downloader = FTPDownloader(
        hostname='ftp.terminalvideo.com',
        username='MultiplShopp',
        password='Tvide0Ftp258',
        silently_encode=False)

    parser = CSVParser(
        delimiter=';',
        skip_first=True)

    mapping = Adapter(
        barcode='Cod. barre',
        name='Titolo',
        description='Trama',
        price=lambda self, item: float(item['Pvc'].replace(',', '.')) if item['Pvc'] else None,
        image='Img Lrg Web',
        date=lambda self, item: datetime.strptime(item['Data primo rilascio'], '%d/%m/%Y') if item['Data primo rilascio'] else None,
        supplier_code='Cod. interno',
        supplier_price=lambda self, item: float(item['Listino'].replace(',', '.')) / 100.0 * (100 - DISCOUNTS.get(item['Categoria sconto'], 0)) if item['Listino'] else None,
        supplier_quantity=lambda self, item: item['Q.ta in stock'] or 0)

    def validate(self, item):
        assert item['Tipo record'] != 'E'
        assert float(item['Pvc'].replace(',', '.')) > 0
        assert item['Formato'] != 'Audio Cd'
        assert 'rental)' not in item['Titolo'].lower()

    def group(self, item):
        group_name = item['Titolo'].rsplit('(', 1)[0].strip() if '(' in item['Titolo'] and item['Titolo'][-1] == ')' else item['Titolo']

        if item['_file'] == 'Merchandising':
            if '(' in item['Titolo'] and item['Titolo'][-1] == ')':
                extra = item['Titolo'].rsplit('(', 1)[1].strip()
                extra = extra.replace('Tg. %s' % item['Taglia'], '')
                extra = extra.replace(item['Genere T-Shirt'], '')

                group_key = ''.join([item['_file'], item['Formato'], item['Genere principale'], group_name, extra])
                group_key = re.sub(r' +', ' ', group_key)
                group_key = md5(group_key).hexdigest()

                return group_key, group_name

        if item['_file'] == 'HomeVideo':
            group_key = ''.join([item['_file'], item['Genere principale'], group_name])
            group_key = re.sub(r' +', ' ', group_key)
            group_key = md5(group_key).hexdigest()

            return group_key, group_name
