# -*- coding: utf-8 -*-
{
    'name': "NetAddiction Reset Catalog",
    'summary': "Serve a resettare il catalogo",

    'description': """
1 - Disattivare tutti i prodotti a catalogo (tasto Acceso-Spento). [*IDEA: spegnimento delle schede, le schede non attive non si vedono a backoffice ma rimangono visibili sul front end (modifica front end veloce) in modo da non far incazzare google??? in questo modo la gestione catalogo backoffice diviene più semplice*]
2 - Azzerare tutte le quantità fornitori all'interno di tutte le schede prodotto.
3 - Mettere l'intero catalogo in "Esaurito"
4 - Mettere in "Acquistabile" i prodotti con "Quantità disponibile" >0
5 - Inserire a tutti i prodotti del passaggio 5 "quantità limite" a 0+Non vendibile, una volta arrivati a 0 il "non vendibile" si dovrebbe levare da solo.
6 - Mettere in "Acquistabile" i prodotti con una data di prenotazione, quindi >"al giorno in cui vi trovate". Unica limitazione fatta per le "Quantità Limite" già arrivate alla quantità richiesta (es. Collector di sta minchia a -70 non vendibile, se sta già con "quantità disponibile" a -70 non va rimessa "Acquistabile)
    """,
    'author': "Netaddiction",

    'website': "http://www.netaddiction.it",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['base', 'product', 'sale', 'purchase', 'mrp', 'account'],
    'data': [
        
    ],
    'application': True,
}
