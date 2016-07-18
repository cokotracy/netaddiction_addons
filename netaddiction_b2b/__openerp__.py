# -*- coding: utf-8 -*-
{
    'name': "NetAddiction B2B",
    'summary': "Modulo di abilitazione al B2B",

    'description':"""
    GEstione del B2B
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1',
    'depends': ['base','product','sale','purchase','mrp','account','netaddiction_products','netaddiction_special_offers','delivery','netaddiction_orders','netaddiction_warehouse'],
    'data': [
        'views/customers.xml',
        'views/pricelist.xml',
        'views/orders.xml',
        'data/report.xml',
        'data/bolla_b2b.xml',
        'views/wave.xml'
    ]
}