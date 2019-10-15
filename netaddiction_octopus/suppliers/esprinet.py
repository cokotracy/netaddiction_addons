from ..base import supplier
from ..base.adapter import Adapter
from ..base.downloaders import FTPDownloader
from ..base.parsers import CSVParser


class Esprinet(supplier.Supplier):
    files = [
        {
            'name': 'Main',
            'mapping': (
                ('dispoP.txt.zip', (
                    'Codice',
                    'CodiceProduttore',
                    'CodiceEAN',
                    'Prod',
                    'DescProd',
                    'NomeCasaProd',
                    'Tipo',
                    'CatMerc',
                    'DescCatMerc',
                    'Fam',
                    'DescFam',
                    'GrMaster',
                    'DescGrMaster',
                    'Dispo',
                    'Arrivi',
                    'Stato',
                    'Descrizione',
                    'DescEstesa',
                    'PrezzoListino',
                    'PrezzoRivenditore',
                    'ScontoDealerStandard',
                    'PrezzoPromo',
                    'DataPromoDa',
                    'DataPromoA',
                    'PesoLordo',
                    'Altezza',
                    'Lunghezza',
                    'Profondita',
                    'Raee',
                    'Modello',
                    'TempoDOAEsprinet',
                    'TempoGaranziaEsprinet',
                    'TempoDOAEndUser',
                    'TempoGaranziaEndUser',
                    'StreetPrice',
                    'QtaMinimaOrd',
                )),
            ),
        },
    ]

    downloader = FTPDownloader(
        hostname='dataservice.esprinet.com',
        username='1-W25951',
        password='oEUBaHKLTN3sy7f2GOFa')

    parser = CSVParser(
        skip_first=True,
        delimiter='|')

    mapping = Adapter(
        barcode='CodiceEAN',
        name='Descrizione',
        description='DescEstesa',
        supplier_code='Codice',
        supplier_price=lambda self, item: float(item['PrezzoRivenditore']),
        supplier_quantity='Dispo')
