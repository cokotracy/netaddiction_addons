# -*- coding: utf-8 -*-
{
    "name": "Netaddiction Website Stock Notification",
    "summary": """
        Netaddiction Website Stock Notification
    """,
    "author": "Netaddiction",
    "category": "Custom Development",
    "version": "14.0.0.1.0",
    "description": """
        This module will add feature on ecommerce 'notify me when product will be available.'
        Credit: OCA
    """,
    "depends": ["website_sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/website_stock_views.xml",
        "views/website_template.xml",
    ],
    "installable": True,
    "application": False,
}
