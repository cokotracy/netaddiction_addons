# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Purchase",
    'summary': "Purchase Order Management for Netaddiction",
    'author': "OpenForce",
    'website': "http://www.openforce.it",
    'category': 'Purchase',
    'version': '13.0.2.1.0',
    'depends': [
        'web',
        # 'base',
        'product',
        # 'sale',
        'purchase',
        # 'mrp',
        # 'account',
        'netaddiction_products',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/template_email.xml',
        'data/cron.xml',
        'views/assets.xml',
        'views/actions_client.xml',
    #     'views/purchase_product_list.xml',
    #     'views/purchase_order_line.xml',
        'views/res_partner.xml',
    #     'views/wave.xml',
    #     'views/move.xml',
        'views/do_purchase_product.xml',
        # Leave menus for last to upload every action and view beforehand
        'views/menus.xml',
    ],
    'qweb': [
         "static/src/xml/*.xml",
    ],
    'application':True,
}
