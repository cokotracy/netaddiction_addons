{
    'name': "NetAddiction Customer",
    'summary': """NetAddiction customizations to partners and customers""",
    'author': "Rapsodoo",
    'website': "https://www.rapsodoo.com",
    'category': 'Hidden',
    'version': '14.0.1.2.0',
    'depends': [
        'base',
        'affiliate_management',
    ],
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
    ]
}
