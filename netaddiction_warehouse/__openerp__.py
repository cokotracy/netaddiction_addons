# -*- coding: utf-8 -*-

{
    'name': "Netaddiction Warehouse",
    'summary': "Magazzino Netaddiction",
    'description': """

    """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Warehouse Management',
    'version': '1.0',
    'depends': [
        'base', 'product', 'sale', 'sale_stock', 'purchase',
        'mrp', 'stock', 'netaddiction_products', 'web', 'delivery',
        'netaddiction_special_offers', 'netaddiction_orders',
        'netaddiction_payments'
    ],
    'data': [
        'data/cron.xml',
        'data/subtype_mail.xml',
        'data/carriers.xml',
        'views/locations.xml',
        'templates/top_menu.xml',
        'templates/inventory_app.xml',
        'templates/assets.xml',
        'templates/search.xml',
        'templates/allocation.xml',
        'templates/pick_up.xml',
        'views/menu.xml',
        'views/report.xml',
        'views/bolla_di_spedizione.xml',
        'views/controllo_pickup.xml',
        'views/settings_menu.xml',
        'views/orders.xml',
        'views/delivery.xml',
        'views/partner.xml',
        'views/products.xml',
        'views/manifest.xml',
        'views/time_settings.xml',
        'views/autopreparation.xml',
        'views/products_movement.xml',
        'views/move.xml'
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'application': True,
}
