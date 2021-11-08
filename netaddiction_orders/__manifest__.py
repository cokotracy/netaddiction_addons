# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Orders',
    'version': '14.0.1.6.2',
    'category': 'Sale',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'mail',
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
