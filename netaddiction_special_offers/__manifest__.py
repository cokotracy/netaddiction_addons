# Copyright 2020 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Special Offers',
    'summary': "Offers and discount for multiplayer.com",
    'version': '14.0.1.0.0',
    'category': 'Sale',
    'website': 'http://www.netaddiction.it',
    'author': 'Netaddiction',
    'license': 'LGPL-3',
    'depends': [
        'coupon',
        'sale_coupon',
        'sale',
        'product',
        # 'base',
        # 'purchase',
        # 'mrp',
        # 'stock',
        # 'netaddiction_customer',
        # 'netaddiction_customer_care'
    ],
    'data': [
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'views/digital_bonus.xml',
        'views/coupon_program.xml',
        'views/sale_order.xml',
        # 'views/minimum.xml',
        # 'data/acl_minimum.xml'
    ],
    'installable': True
}
