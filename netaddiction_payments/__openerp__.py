# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Payments",
    'summary': "Nuova Gestione Pagamenti",

    'description':"""
    Modulo della gestione degi pagamenti
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base','product','sale','purchase','mrp','account'],
    'data' : [
        'views/account_payment.xml',
        'views/paypal_configuration.xml',
        'data/paypal_salt.xml',
        'data/account_journal.xml',
    ]
}
