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
    'version': '1.1',
    'data': [
        'data/user_group_cc.xml',
        'views/project_issue.xml',
        'views/settings_company_mail.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'data/workflow.xml',
        'views/issue_report.xml',
        'views/product.xml',
    ],
    'qweb': ['static/src/xml/template.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
