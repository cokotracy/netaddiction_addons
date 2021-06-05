{
    'name': "NetAddiction Octopus",
    'summary': "Importa e tiene aggiornati i prodotti prendendo le"
               " informazioni dai fornitori",
    'description': """""",
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Extra Tools',
    'depends': [
        'base',
        'product',
        'purchase',
        'netaddiction_products',
    ],
    'version': '13.0.2.0.0',
    'data': [
        'data/cron.xml',
        'views/octopus.xml',
        'views/octopus_category.xml',
        'views/octopus_supplier.xml',
        'views/octopus_product.xml',
        'views/octopus_tax.xml',
        'views/octopus_autoimport.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
