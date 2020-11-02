{
	'name': 'Netaddiction Website Enhancement',
    'summary': """
        Netaddiction Website Enhancement
    """,
    'author': "OpenForce",
    'category': 'Custom Development',
    'version': '13.0.1.0.0',
    'description': """
        This module will enhance the website features
        - Layout similar to multiplayer.com
        - Product Filter options
        - Product Order by options
        - Product Filter by range slider
    """,
	'depends': [
        'website_sale'
    ],
    'data': [
    	'views/base_template.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/products.xml',
        'views/product_template_views.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
	'installable': True,
    'application': False,
}
