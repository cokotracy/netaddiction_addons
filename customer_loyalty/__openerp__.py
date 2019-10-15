# -*- coding: utf-8 -*-
{
    'name': "Customer Loyalty - Fidelizzazione clienti - Raccolta punti",
    'summary': "",

    'description': """
        Accumulare punti ogni ordine
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'account', 'stock'],
    'data': [
        'views/customer_loyalty.xml',
        'data/cron.xml',
    ]
}
