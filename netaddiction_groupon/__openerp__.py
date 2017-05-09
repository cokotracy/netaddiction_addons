# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Groupon",
    'summary': "Grouponmultiplayer.com",
    'description': """
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'stock', 'netaddiction_products', 'netaddiction_warehouse'],
    'data': [
        'data/groupon_location.xml',
        'data/ir_values.xml',
        'views/locations.xml',
        'views/assets.xml',
        'views/wave.xml',
        'templates/groupon.xml',
        'views/orders.xml',
        'data/menu.xml',
        'data/acl.xml',
        'views/config.xml',
        'views/manifest.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
