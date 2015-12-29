# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Customer",
    'summary': "Funzionalità per i clienti di multiplayer.com",
    'description':"""
    Aggiunge i seguenti campi ai customers: indirizzo di default, rating, azienda, email rating, lista dei gift e totale dei gift. Aggiunge Gift, gift type e affiliate. Viste comprese
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base','product','sale','purchase','mrp','stock'],
    'data' :[
        'views/partner.xml',
        'views/gift.xml',
        'data/gift_type_data_entry.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
