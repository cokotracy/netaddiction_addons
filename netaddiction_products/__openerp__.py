# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Products",
    'summary': "Prodotti",

    'description':"""
    Gestione Prodotti
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1',
    'depends': ['base','product','sale','purchase','mrp','account'],
    'data': [
        'views/assets.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/api_set_extra_data.xml'
    ]
}