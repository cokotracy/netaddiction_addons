# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Ebay",
    'summary': "Modulo ebay per multiplayer.com",
    'description': """
    Permette di gestire automaticamente il catalogo ebay
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'stock', 'netaddiction_products'],
    'data': [
        'views/product.xml',
        'views/config.xml',
        'views/orders.xml',
        'data/ir_values.xml',
        'data/crons.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
