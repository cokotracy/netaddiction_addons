# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Extra Fields",
    'summary': "Aggiunge campi extra ad alcuni moduli",

    'description':"""
    Aggiunge campi extra ad alcuni moduli per il corretto funzionamento degli shop\n
    Aggiunge viste personalizzate\n
        \n
        * *RES.PARTNER* aggiunto campo 'is_default_delivery_address.'
        * *PRODUCT* il prezzo il tipo e i fornitori diventano indipendenti dal template,
            il prezzo si inserisce ivato e all'atto del salvataggio gli scorpora l'iva,aggiunte quantità disponibile
            e quantità totale fornitori.
        * Modifica la vista dei PARTNER per mettere nei clienti l0indirizzo di default, aggiorna la vista
            dei partner secondo le nuove regole.
        * Piccole modifiche alla vista prodotti, aggiunge i campi nuovi""",
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.5',
    'depends': ['base','product','sale','purchase','mrp'],
    'data' :[
        'view/product.xml',
        'view/partner.xml',
    ],
}
