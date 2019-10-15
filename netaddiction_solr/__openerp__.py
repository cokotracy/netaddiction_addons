# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Solr",
    'summary': "Implementa un motore di ricerca dei prodotti basato su Solr",
    'description': """""",
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Sales Management',
    'depends': ['base', 'netaddiction_products'],
    'version': '0.1',
    'data': [
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
