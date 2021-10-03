{
    "name": "Netaddiction Website",
    "summary": """
        Netaddiction Website
    """,
    "author": "Netaddiction",
    "category": "Custom Development",
    "version": "14.0.1.1.0",
    "description": """
        This module will enhance the odoo features
    """,
    "depends": ["website_sale"],
    "data": [
        "data/cron.xml",
        "views/web/product.xml",
        "views/web/homepage.xml",
    ],
    "installable": True,
    "application": False,
}
