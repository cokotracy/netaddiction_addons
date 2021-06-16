# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Partner - GDPR',
    'version': '14.0.1.0.0',
    'category': 'Contact',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/partner_gdpr_disable.xml',
        'views/sale.xml',
        'views/partner.xml',
    ],
}
