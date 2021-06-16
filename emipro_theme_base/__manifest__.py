# -*- coding: utf-8 -*-
{
    # Theme information
    'name': 'Emipro Theme Base',
    'category': 'Base',
    'summary': 'Base module containing common libraries for all Emipro eCommerce themes.',
    'version': '2.5.1',
    'license': 'OPL-1',
    'depends': [
        'website_sale_wishlist',
        'website_sale_comparison',
        'website_blog',
    ],

    'data': [
        'data/slider_styles_data.xml',
	    'templates/template.xml',
        'templates/product_snippet_popup.xml',
        'templates/brand_category_snippet_popup.xml',
        'templates/pwa.xml',
        'templates/assets.xml',
	    'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/product_template.xml',
        'views/product_attribute_value_view.xml',
        'views/product_public_category.xml',
        'wizard/product_brand_wizard_view.xml',
        'templates/image_hotspot_popup.xml',
    ],
    'qweb': ['static/src/xml/advanced_search.xml'],

    # Odoo Store Specific
    'images': [
        'static/description/emipro_theme_base.jpg',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 9.00,
    'currency': 'EUR',
}
