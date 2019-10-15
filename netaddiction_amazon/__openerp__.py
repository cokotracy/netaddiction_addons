# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Amazon",
    'summary': "Modulo amazon mws per multiplayer.com",
    'description': """
    Permette di gestire automaticamente il catalogo amazon
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'stock', 'netaddiction_products'],
    'data': [
        'views/product.xml',
        # 'views/config.xml',
        # 'views/orders.xml',
        # 'data/ir_values.xml',
        # 'data/crons.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
