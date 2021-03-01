# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Products',
    'version': '13.0.3.3.0',
    'category': 'Product',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'stock',
        'purchase',
        'website_sale',
    ],
    'data': [
        'views/product_views.xml',
        'data/template_email.xml',
    ],
}
