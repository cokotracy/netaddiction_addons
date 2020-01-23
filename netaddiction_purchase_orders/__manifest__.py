# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Purchase",
    'summary': "Purchase Order Management for Netaddiction",
    'author': "OpenForce",
    'website': "http://www.openforce.it",
    'category': 'Purchase',
    'version': '12.0.1.1.0',
    'depends': [
        # 'base',
        'product',
        # 'sale',
        'purchase',
        # 'mrp',
        # 'account',
        'netaddiction_products',
        ],
    'data' : [
    #     'views/purchase_product_list.xml',
    #     'views/purchase_order_line.xml',
        'views/res_partner.xml',
        # 'data/cron.xml',
    #     'views/wave.xml',
    #     'views/move.xml',
        'views/do_purchase_product.xml'
    #     ],
    # 'qweb':[
    #     "static/src/xml/*.xml",
        ],
    'application':True,
}
