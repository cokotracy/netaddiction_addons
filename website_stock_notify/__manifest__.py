# -*- coding: utf-8 -*-
{
    'name': "Website Stock Notification",
    'summary': """
        Website Stock Notification
    """,
    'author': "OpenForce",
    'category': 'Custom Development',
    'version': '1.0',
    'description': """
        This module will add feature on ecommerce 'notify me when product will be available.'
    """,
    'depends': ['website_sale_stock'],
    'data': [
        'security/ir.model.access.csv',

        'data/data.xml',

        'views/website_stock_views.xml',
        'views/website_template.xml',
    ],

    'installable': True,
    'application': False,
}
