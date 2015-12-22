# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Doozy",
    'summary': "Piccole migliorie all'interfaccia",
    'description': """
    """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'depends': ['base', 'product', 'mrp', 'netaddiction_extra_fields','stock','web'],
    'version': '0.1',
    'data': [
        'views/product_template.xml',
        'views/product_product.xml',
        'views/partner.xml',
        'views/gift.xml',
        'data/menu.xml',
    ],
    'qweb': ['static/src/xml/template.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
