# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Inventory APP",

    'summary': """Applicazione mobile per il magazzino""",

    'description': """
        Applicazione mobile per il magazzino
    """,

    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','sale','mrp','purchase','stock'],

    'data' :[
        'templates/inventory_app.xml',
        'templates/assets.xml',
        'views/menu.xml',
    ]
}
