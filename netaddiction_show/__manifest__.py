# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "NetAddiction Show",
    'summary': "Gestione Fiere",
    'description': """
    Modulo della gestione delle fiere
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Sale',
    'version': '12.0.1.0.0',
    'depends': [
        # 'base',
        'product',
        'stock',
        # 'sale',
        # 'purchase',
        # 'mrp',
        # 'account',
        # 'netaddiction_warehouse',
        # 'netaddiction_acl',
        ],
    'data': [
        # 'data/data_show.xml',
        'views/menu.xml',
        'views/show.xml',
        # 'data/acl.xml',
        # 'templates/assets.xml',
        # 'templates/show_app.xml',
        'security/ir.model.access.csv',
        ],
}
