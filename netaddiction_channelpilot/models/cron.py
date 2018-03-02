# -*- coding: utf-8 -*-
from openerp import api, models
from ..settings import DOMAIN_AVAILABLE, SUPPLIERS, SUPPLIERS_AVAILABLE, OFF_DOMAIN, SUPPLIERS_OFF

import xml.etree.cElementTree as ET

class FeedCron(models.Model):
    _name = 'netaddiction.cp.feedcron'

    @api.model
    def switch_on(self):
        # Questo cron serve per controllare l'accensione su ChannelPilot

        # Cerco i prodotti attivi, sale_ok true, disponibili in magazzino con channelpilot False
        available_products = self.env['product.product'].search(DOMAIN_AVAILABLE)
        # attivo in channelpilot i prodotti in magazzino
        if len(available_products) > 0:
            available_products.write({'channelpilot': True})
            self.env.cr.commit()
        # Cerco i prodotti con i fornitori > tot che non sono accesi su ChannelPilot
        for supplier in SUPPLIERS:
            domain = SUPPLIERS_AVAILABLE + [('name', '=', int(supplier)), ('avail_qty', '>=', int(SUPPLIERS[supplier]))]
            results = self.env['product.supplierinfo'].search(domain)
            for res in results:
                res.product_id.channelpilot = True
            self.env.cr.commit()
        return True

    @api.model
    def switch_off(self):
        # Serve per controllare lo spegnimento su ChannelPilot
        # in base a come si comporta CP usiamo blacklist o channelpilot si/no

        # spegno i prodotti che sono andati cin sale_ok = False
        results = self.env['product.product'].search(OFF_DOMAIN)
        if len(results) > 0:
            results.write({'channelpilot': False})
            self.env.cr.commit()

        # prendo i prodotti con qty_fornitore < tot e che sono in channelpilot
        for supplier in SUPPLIERS:
            domain = SUPPLIERS_OFF + [('name', '=', int(supplier)), ('avail_qty', '<', int(SUPPLIERS[supplier]))]
            results = self.env['product.supplierinfo'].search(domain)
            for res in results:
                # oppure lo rimuovi da cp oppure channelipilot = False
                # se il prodotto non è in magazzino
                if res.product_id.qty_available_now <= 0:
                    res.product_id.channelpilot = False
            self.env.cr.commit()
