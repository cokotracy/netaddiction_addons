# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Special Offers",
    'summary': "Funzionalità per le offerte multiplayer.com",
    'description':"""
    Permette di creare offerte speciali sul catalogo prodotti e sul carrello.
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base','product','sale','purchase','mrp','stock','netaddiction_expressions','netaddiction_customer','netaddiction_customer_care'],
    'data' :[
        'views/special_offers.xml',
        'views/offer_product.xml',
        'views/digital_bonus.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
