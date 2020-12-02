# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Payments",
    'summary': "Nuova Gestione Pagamenti",

    'description': """
    Modulo della gestione degi pagamenti
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'account', 'netaddiction_products'],
    'data': [
        'views/account_payment.xml',
        'views/paypal_configuration.xml',
        'views/positivity_configuration.xml',
        'views/ccdata.xml',
        'views/positivity_executor.xml',
        'views/cod_register.xml',
        'views/sale.xml',
        'views/stock.xml',
        'views/sofort_configuration.xml',
        'views/stripe_configuration.xml',
        'data/paypal_salt.xml',
        'data/positivity_salt.xml',
        'data/account_journal.xml',
        'data/cash_on_delivery.xml',
        'data/sofort_salt.xml',
        'data/stripe_salt.xml',

    ]
}
