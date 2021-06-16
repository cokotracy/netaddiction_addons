# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Reset Catalog',
    'version': '14.0.1.0.0',
    'category': 'Product',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
}
