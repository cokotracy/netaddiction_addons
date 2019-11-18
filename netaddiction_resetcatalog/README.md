Netaddiction - Reset Catalog
============================

Descrizione del modulo originale
--------------------------------

**Versione precedente**: 9.0

**Funzione**: run_reset

**File**: *models/reset_catalog.py*

    1 - Disattivare tutti i prodotti a catalogo (tasto Acceso-Spento).
    2 - Azzerare tutte le quantità fornitori all'interno di tutte le schede prodotto.
    3 - Mettere l'intero catalogo in "Esaurito"
    4 - Mettere in "Acquistabile" i prodotti con "Quantità disponibile" >0
    5 - Inserire a tutti i prodotti del passaggio 5 "quantità limite" a 0+Non vendibile, una volta arrivati a 0 il "non vendibile" si dovrebbe levare da solo.
    6 - Mettere in "Acquistabile" i prodotti con una data di prenotazione, quindi >"al giorno in cui vi trovate". Unica limitazione fatta per le "Quantità Limite" già arrivate alla quantità richiesta (es. Collector di sta minchia a -70 non vendibile, se sta già con "quantità disponibile" a -70 non va rimessa "Acquistabile)
    7 - RIACCENDERE I PRODOTTI SERVIZIO (ATTIVO, ACQUISTABILE, NASCOSTO)
