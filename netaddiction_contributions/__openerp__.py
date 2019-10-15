# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Contributions",
    'summary': "Modulo di gestione Contributi",

    'description':"""
    Gestione dei contributi
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1',
    'depends': ['base','product','sale','purchase','mrp','account','netaddiction_products',
        'netaddiction_purchase_orders','netaddiction_account','netaddiction_warehouse'],
    'data': [
        'views/contribution.xml',
        'views/orders.xml',
        'data/cron.xml',
        'data/contribution_product.xml'
    ]
}