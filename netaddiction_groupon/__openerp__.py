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
        'views/locations.xml',
        'data/menu.xml',
        'data/acl.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
