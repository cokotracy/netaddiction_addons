# -*- coding: utf-8 -*-

{
    'name': "NetAddiction Customer Care",
    'summary': "Customer Care Per Odoo",
    'description': """
    """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'depends': ['base', 'product', 'project','project_issue','stock','sale'],
    'version': '1.0',
    'data': [
        'data/user_group_cc.xml',
        'views/project_issue.xml',
    ]
}
