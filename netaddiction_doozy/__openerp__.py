# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Doozy",
    'summary': "Piccole migliorie all'interfaccia",
    'description': """
    Viene caricato un nuovo css\n\n
    BUTTON COLOR\n
    - net_orange \n
    - net_green \n
    - net_red \n
    - net_blue \n
    """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'depends': ['base', 'product', 'mrp', 'netaddiction_extra_fields','stock','web'],
    'version': '0.1',
    'data': [
        'data/menu.xml',
        'data/load_css.xml'
    ],
    'qweb': ['static/src/xml/template.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
