# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Octopus",
    'summary': "Importa e tiene aggiornati i prodotti prendendo le informazioni dai fornitori",
    'description': """""",
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Extra Tools',
    'depends': ['base', 'product', 'netaddiction_products'],
    'version': '0.1',
    'data': [
        'data/cron.xml',
        'views/octopus.xml',
        'views/octopus_category.xml',
        'views/octopus_supplier.xml',
        'views/octopus_product.xml',
        'views/octopus_tax.xml',
        'views/autoimport.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
