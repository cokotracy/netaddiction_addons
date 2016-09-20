# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Show",
    'summary': "Gestione Fiere",

    'description': """
    Modulo della gestione delle fiere
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'account', 'netaddiction_warehouse', 'netaddiction_acl'],
    'data': [
        'data/data_show.xml',
        'views/menu.xml',
        'views/show.xml',
        'data/acl.xml',
        'templates/assets.xml',
        'templates/show_app.xml'
    ],
    'application': True,
}
