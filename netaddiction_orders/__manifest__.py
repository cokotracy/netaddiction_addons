# Copyright 2019-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Orders',
    'version': '14.0.1.2.0',
    'category': 'Sale',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'website',
        'website_sale',
        'payment',
        'netaddiction_payments',
        'affiliate_management',
    ],
    'data': [
        'data/template_email.xml',
        'views/assets.xml',
        'views/partner.xml',
        'views/sale.xml',
        'templates/payment.xml',
    ],
}
