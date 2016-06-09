from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


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
            'Cod. barre',  # Barcode
            'Cod. interno',
            'Codice',
            'Codice sottoformato',  # ext1
            'Collana',
            'Colore',
            'Contenuti extra',
            'Data aggiornamento immagine',
            'Data fine offerta',
            'Data primo rilascio',
            'Data rilascio',
            'Distribuzione',
            'Durata',
            'Fascia eta',  # ext2
            'Formato',
            'Formato audio',
            'Formato secondario',
            'Formato video',
            'Genere',
            'Genere principale',
            'Img Lrg Web',  # Img
            'Immagine',
            'Iva',  # IVA
            'Lingue',
            'Listino',  # Listino 1
            'Pvc',  # Listino 5
            'Marca',
            'Nazione',
            'Numero supporti',
            'Offerta',
            'Premi',
            'Regia',
            'Sistema TV',  # Sistema tv
            'Sottotitoli',
            'Stato vendite',
            'Titolo',
            'Titolo originale',  # Titolo Originale
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

    categories = 'Formato', 'Genere principale'

    downloader = FTPDownloader(
        hostname='ftp.terminalvideo.com',
        username='MultiplShopp',
        password='Tvide0Ftp258')

    parser = CSVParser(
        delimiter=';',
        skip_first=True)

    mapping = Adapter(
        barcode='Cod. barre',
        supplier_code='Cod. interno',
        name='Titolo',
        description='Trama')

    def validate(self, item):
        assert item['Tipo record'] != 'E'
        assert float(item['Pvc'].replace(',', '.')) > 0
        assert item['Formato'] != 'Audio Cd'
