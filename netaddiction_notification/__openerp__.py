# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Notification",
    'summary': "Notifica nel log le modifiche effettuate",
    'description':"""
    Log per le modifiche
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.5',
    'depends': ['base','product','sale','purchase','mrp','account','mail'],
    'data' :[
        'views/resconfigview.xml',
    ]
}
