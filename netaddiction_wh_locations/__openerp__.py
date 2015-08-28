# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Warehouse Locations",
    'summary': "Multi locations per prodotto nel magazzino",
    'description':"""
    Aggiunge le locazioni (scaffali) nel magazzino a cui associare qty e id prodotto
    ogni locazione ha un nome, un barcode e prodotti assocciati con relative quantità
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base','product','sale','purchase','mrp','stock'],
    'data' :[
        'views/locations.xml',
        'views/products.xml'
    ]
}
