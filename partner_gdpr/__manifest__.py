# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Partner - GDPR',
    'version': '13.0.1.0.0',
    'category': 'Contact',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'contacts',
    ],
    'data': [
        'wizard/partner_gdpr_disable.xml',
        'views/sale.xml',
        'views/partner.xml',
    ],
}
