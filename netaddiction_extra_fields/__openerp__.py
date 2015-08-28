# -*- coding: utf-8 -*-
{
    'name': "Netaddiction Extra Fields",
    'summary': "Aggiunge campi extra ad alcuni moduli",
    'description':"""Aggiunge campi extra ad alcuni moduli per il corretto funzionamento degli shop\n
    Aggiunge viste personalizzate\n
        \n
    RES.PARTNER:\n
        - campi: aggiunge 'is_default_delivery_address' per settare quell'indirizzo come default\n
        - viste: estende vista form\n
    PRODUCT.PRODUCT:\n
        - campi: rende indipendenti i campi 'type','list_price' e 'lst_price' dal template, aggiunge 'out_date' (data di uscita),'out_date_approx_type'(approssimazione per la data),'published' (visibile sul sito)\n
        - vista: estende vista form\n
    PRODUCT.TEMPLATE:\n
        - campi: aggiunge al campo 'type' il valore 'stockable', aggiunge 'out_date' (data di uscita),'out_date_approx_type'(approssimazione per la data),'published' (visibile sul sito)\n
        - vista: estende vista form\n
    SALE.ORDER.LINE:\n
        - override metodo 'product_id_change' per mettere prezzo giusto nel campro price_unit della linea d'ordine dopo aver effettuato la modifica del campo lst_price nel modello product
    """,
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
