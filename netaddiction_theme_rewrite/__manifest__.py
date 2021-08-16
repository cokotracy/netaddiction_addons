# Copyright 2021 Netaddiction

{
    'name': 'Netaddiction Theme Rewrite',
    'category': 'eCommerce',
    'version': '14.0.1.0.0',
    'author': 'Netaddiction',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'web',
        'website',
        'website_sale',
        'odoo_website_wallet',
        'product_template_tags',
    ],
    'data': [
        'templates/assets.xml',
        'templates/template_home.xml',
        'templates/template_category.xml',
        'templates/template_product.xml',
        'templates/template_privacy_policy.xml',
        'templates/template_shipping_terms.xml',
        'templates/template_tag.xml',
        'templates/template_wallet.xml',
        'templates/google-snippet/product.xml'
    ],
    # Technical
    'installable': True,
}
