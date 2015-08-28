# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Extra Fields",
    'summary': "Aggiunge campi extra ad alcuni moduli",
    'description':"""Aggiunge campi extra ad alcuni moduli per il corretto
        funzionamento degli shop\n

        PRODUCT.PRODUCT:\n

        1 - Override dei campi 'type' = 'ogni variante può essere un tipo differente'
        2 - Aggiunta campi 'published' = 'visibile o no sul sito',
            'out_date' = 'Data di uscita',
            'out_date_approx_type' = 'tipo di approssimazione sulla data'
        """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.1',
    'depends': ['base','product','sale','purchase','mrp'],
    'data' :[
        'view/product.xml',
        'view/partner.xml'
    ]
}
