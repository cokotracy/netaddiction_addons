{
    "name": "Netaddiction Enhancement",
    "summary": """
        Netaddiction Enhancement
    """,
    "author": "Netaddiction",
    "category": "Custom Development",
    "version": "1.0.0",
    "description": """
        This module will enhance the odoo features
    """,
    "depends": ["website_sale"],
    "data": [
        "data/cron.xml",
        "views/web/product.xml",
        "views/web/homepage.xml",
    ],
    # "qweb": ["static/src/xml/*.xml"],
    "installable": True,
    "application": False,
}
