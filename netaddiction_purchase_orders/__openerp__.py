# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Purchase",
    'summary': "Nuova Gestione purchase.orders",

    'description':"""
    Modulo della gestione degli ordini di acquisto verso i fornitori
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base','product','sale','purchase','mrp','account','netaddiction_customer'],
    'data' : [
        'views/purchase_product_list.xml',
        'views/purchase_order_line.xml',
        'views/res_partner.xml',
        'data/cron.xml',
        'views/wave.xml',
        'views/move.xml',
        'views/do_purchase_product.xml'
    ],
    'qweb':[
        "static/src/xml/*.xml",
    ],
    'application':True,
}
