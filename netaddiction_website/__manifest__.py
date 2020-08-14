{
	'name': 'Offshore App',
	'depends': [
		'base',
        'website',
        'sale',
        'website_sale'
    ],
    'data': [
    	'views/base_template.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/products.xml',
    ],
	'installable': True,
    'application': True,
    'auto_install': True,
}