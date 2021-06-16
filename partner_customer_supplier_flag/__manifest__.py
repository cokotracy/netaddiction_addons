# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Partner - Customer and Supplier Flags",
    'summary': "This module adds the flags to set a partner as a supplier"
               " and/or a customer",
    'version': '14.0.1.0.0',
    'category': 'Contacts',
    'website': 'http://www.openforce.it',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/partner.xml',
    ],
    'installable': True
}
