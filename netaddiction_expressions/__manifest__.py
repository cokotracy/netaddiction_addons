# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Expressions',
    'version': '12.0.1.0.0',
    'category': 'Product',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'sale_management',
        'stock',
        'mrp',
    ],
    'data': [
        'views/expression_views.xml',
        'views/product_views.xml',
        'security/ir.model.access.csv',
    ],
}
