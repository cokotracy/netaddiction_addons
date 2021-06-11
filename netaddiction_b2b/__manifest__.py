# Copyright 2019-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction B2B',
    'version': '13.0.2.1.0',
    'category': 'Sale',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'sale_management',
        'netaddiction_expressions',
        'netaddiction_products',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/config_views.xml',
        'views/product_views.xml',
        'views/orders.xml',
        'data/cron.xml',
    ],
}
