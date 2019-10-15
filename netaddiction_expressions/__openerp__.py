# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Expressions",
    'summary': "Funzionalità per creare espressioni booleane su categorie e attributi",
    'description':"""
    Permette di individuare insiemi di prodottti per offerte e commissioni
    """,
    'author': "Netaddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base','product','sale','purchase','mrp','stock'],
    'data' :[
        'views/expression.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
