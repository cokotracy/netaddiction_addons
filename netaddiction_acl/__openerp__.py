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
    'depends': ['base','product','netaddiction_products','netaddiction_warehouse','netaddiction_purchase_orders',
        'sale','netaddiction_orders','netaddiction_contributions'],
    'data' :[
        'data/delete.xml',
        'data/products_data_entry.xml',
        'data/base_user.xml',
        'data/inventory.xml',
        'data/purchase.xml',
        'data/sale.xml',
        'data/customer_care.xml',
        'data/administration.xml',
        'views/product.xml',
        'views/purchase.xml',
        'views/stock.xml',
        'views/procurement_group.xml',
        'views/res_partner.xml',
        'views/sale.xml',
        'data/god.xml',
    ],
    'application':True,
    

}