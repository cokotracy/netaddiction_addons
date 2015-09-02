# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Doozy",
    'summary': "Piccole migliorie all'interfaccia",
    'description': """
        * Toglie il reference ID dal nome del prodotto
        * Aggiunge il menu Bundle all'area Vendite
        * Nasconde il campo per l'EAN13
    """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'depends': ['base', 'product', 'mrp'],
    'version': '0.1',
    'data': [
        'views/product_view.xml',
    ]
}
