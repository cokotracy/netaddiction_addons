# Copyright 2019-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Orders',
    'version': '13.0.2.0.0',
    'category': 'Sale',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'website',
        'website_sale',
        'payment',
        'netaddiction_payments',
    ],
    'data': [
        'data/template_email.xml',
        'views/assets.xml',
        'views/sale.xml',
        'templates/payment.xml',
    ],
}
