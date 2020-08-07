{
	'name': 'Offshore App',
	'depends': [
		'base',
        'website',
    ],
    'data': [
    	'views/base_template.xml',
        'views/header.xml',
        'views/footer.xml',
    ],
	'installable': True,
    'application': True,
    'auto_install': True,
}