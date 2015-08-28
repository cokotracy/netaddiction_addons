# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Product Bonus",
    'summary': "Funzionalità Prodotti Bonus",
    'description':"""
    PRODOTTI BONUS\n
        - crea il modello 'netaddiction.product.bonus' che estende (delegation) product.product.\n
        - fa ovveride dei metodi 'create','write','unlink' per far si che vengano rispettate tutte le regole e vengano riportati i campi del bonus anche nel prodotto referente.\n
    PRODUCT.PRODUCT:\n
        - aggiunge campo 'bonus_products' e 'is_bonus', il primo mantiene l'ide del bonus referente e il secondo dice se quel prodotto è un bonus

        """,
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '0.5',
    'depends': ['base','product','sale','purchase','mrp'],
    'data' :[
        'views/bonus.xml',
        'views/product.xml',
    ]
}
