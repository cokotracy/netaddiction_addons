# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Products',
    'version': '14.0.2.7.0',
    'category': 'Product',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'stock',
        'purchase',
        'website_sale',
        'product_variant_sale_price',
        'coupon',
        'sale_coupon',
    ],
    'data': [
        'views/product_public_category.xml',
        'views/product_views.xml',
        'views/coupon_views.xml',
        'wizard/massive_product_price_change.xml',
        'data/template_email.xml',
        'security/ir.model.access.csv',
    ],
}
