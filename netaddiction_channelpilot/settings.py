# -*- coding: utf-8 -*-
# settings per l'estrazione dei prodotti per la creazione del feed ChannelPilot

# tutti i prodotti attivi, vendibili, visibili con quantità disponibile > 0 e channelpilot ON
DOMAIN_AVAILABLE = [('active', '=', True), ('sale_ok', '=', True), ('visible', '=', True), ('qty_available_now', '>', 0), ('channelpilot', '=', False), ('channelpilot_blacklist', '=', False)]

# i prodotti attivi, vendibili, visibili, channelpilot ON e con i fornitori configurati che hanno quantità > di tot
# cerco per ogni fornitore i prodotti corrispondenti con la query corretta
# li unisco tutti insieme (così evito doppioni)

# id fornitore : qty minima per feed
SUPPLIERS = {
    # DBLine
    38: 5,
    # Esprinet
    # 137: 5,
    # Terminal
    57: 5
}

SUPPLIERS_AVAILABLE = [('product_id.channelpilot', '=', False), ('product_id.sale_ok', '=', True), ('product_id.channelpilot_blacklist', '=', False)]

# SWITCH OFF
OFF_DOMAIN = [('sale_ok', '=', False), ('channelpilot', '=', True)]
SUPPLIERS_OFF = [('product_id.channelpilot', '=', True), ('product_id.sale_ok', '=', True)]

# FEED
FEED_DOMAIN = [('channelpilot', '=', True)]
