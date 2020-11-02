# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction B2B',
    'version': '13.0.1.1.0',
    'category': 'Sale',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'sale_management',
        'netaddiction_expressions',
        'netaddiction_products',
    ],
    'data': [
        'views/config_views.xml',
        'views/product_views.xml',
        'views/pricelist_views.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
}
