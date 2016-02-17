# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Warehouse",
    'summary': "Magazzino Netaddiction",
    'description':"""
     """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base','product','sale','purchase','mrp','stock','netaddiction_products','web'],
    'data' :[
        'views/locations.xml',
        'data/acl.xml',
        'templates/top_menu.xml',
        'templates/inventory_app.xml',
        'templates/assets.xml',
        'templates/search.xml',
        'templates/allocation.xml',
        'templates/pick_up.xml',
        'views/menu.xml',
        'views/report.xml',
        'views/bolla_di_spedizione.xml',
        'views/controllo_pickup.xml'
    ],
    'qweb':[
        "static/src/xml/*.xml",
    ],
    'application':True,
    

}
