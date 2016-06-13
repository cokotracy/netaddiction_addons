# -*- coding: utf-8 -*-
{
    'name': "Netaddiction ACL",
    'summary': "ACL per netaddiction",
    'description':"""
     """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base','product','netaddiction_products','netaddiction_warehouse','netaddiction_purchase_orders'],
    'data' :[
        'data/products_data_entry.xml',
        'data/base_user.xml',
        'data/inventory.xml',
        'data/god.xml',
        'data/purchase.xml',
        'data/sale.xml',
        'views/product.xml',
        'views/purchase.xml',
    ],
    'application':True,
    

}