# -*- coding: utf-8 -*-
{
    'name': "Netaddiction ChannelPilot",
    'summary': "Implementazione di channelpilot",
    'description': """
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'stock', 'netaddiction_products', 'netaddiction_payments'],
    'data': [
        'views/product.xml',
        'views/order.xml',
        'views/account_payment.xml',
        'data/account_journal.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
