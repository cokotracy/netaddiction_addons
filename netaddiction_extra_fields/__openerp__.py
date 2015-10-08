# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Extra Fields",
    'summary': "Aggiunge campi extra ad alcuni moduli",

    'description':"""
    Aggiunge campi extra ad alcuni moduli per il corretto funzionamento degli shop\n
    *product.product\n
    *product.template\n
    *product.supplierinfo\n\n
    Funzionalità:\n
    *Separazione prezzi listino tra template e variant, aggiunta final_price ivato e list_price diventa deivato
    *Separazione listino fornitori tra template e variant
    *Campo pubblicato sul sito
    *Campo data di uscita e approssimazione data
    *Campi quantità somma fornitori e disponibile effettiva
    *Nuovo conteggio varianti (anche active=false) per i template
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.5',
    'depends': ['base','product','sale','purchase','mrp','account'],
    'data': [
        'data/user_group_data_entry.xml',
    ]
}
