# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Doozy",
    'summary': "Piccole migliorie all'interfaccia",
    'description': """
        * Toglie il reference ID dal nome del prodotto
        * Aggiunge il menu Bundle all'area Vendite
        * Nasconde il campo per l'EAN13
        * Nasconde i grouppi store,status e weigth in inventario product.product
        * Modifica la vista Tree dei product.product con i campi corretti
        * Fa delle traduzioni
    """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'depends': ['base', 'product', 'mrp', 'netaddiction_extra_fields'],
    'version': '0.1',
    'data': [
        'views/product_view.xml',
        'views/products_inventory.xml'
    ]
}
