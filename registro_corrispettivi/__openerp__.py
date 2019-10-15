# -*- coding: utf-8 -*-
{
    'name': "Registro Corrispettivi",
    'summary': "",

    'description': """
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'account', 'stock'],
    'data': [
        'views/corrispettivi.xml',
        'views/corrispettivi_view.xml',
        'views/acl.xml'
    ]
}
