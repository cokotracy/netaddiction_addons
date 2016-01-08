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
        'data/user_group_data_entry.xml',
        'views/product_product.xml',
        'views/product_template.xml'
    ]
}