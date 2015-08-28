# -*- coding: utf-8 -*-
{
    'name': "Multiplayer.com Importer Complete",

    'summary': """Tutto quello che serve per importare multiplayer.com""",

    'description': """
        1 - Modello con corrispondenze : id odoo, id multiplayer.com, tipo di entità\n
    """,

    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '0.9',

    # any module necessary for this one to work correctly
    'depends': ['base','product','sale','mrp','purchase'],

    'data' :[
        'view/multicom_importer_menu.xml',
        'view/multicom_importer_view.xml',
    ]
}
