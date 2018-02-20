# -*- coding: utf-8 -*-
from openerp import api, models
import time
import datetime


class ResetCatalog(models.Model):
    """1 - Disattivare tutti i prodotti a catalogo (tasto Acceso-Spento).
    2 - Azzerare tutte le quantità fornitori all'interno di tutte le schede prodotto.
    3 - Mettere l'intero catalogo in "Esaurito"
    4 - Mettere in "Acquistabile" i prodotti con "Quantità disponibile" >0
    5 - Inserire a tutti i prodotti del passaggio 5 "quantità limite" a 0+Non vendibile, una volta arrivati a 0 il "non vendibile" si dovrebbe levare da solo.
    6 - Mettere in "Acquistabile" i prodotti con una data di prenotazione, quindi >"al giorno in cui vi trovate". Unica limitazione fatta per le "Quantità Limite" già arrivate alla quantità richiesta (es. Collector di sta minchia a -70 non vendibile, se sta già con "quantità disponibile" a -70 non va rimessa "Acquistabile)
    7 - RIACCENDERE I PRODOTTI SERVIZIO (ATTIVO, ACQUISTABILE, NASCOSTO)
    """

    _name = 'netaddiction.reset.catalog'

    @api.model
    def run_reset(self):
        start = time.time()
        # spegnimento [active=False, sale_ok=False] tutti prodotti eccetto quelli presenti in magazzino e tipologia servizio.
        print '[RESET] - Parto ed estraggo i prodotti da disattivare'
        products_to_deactivate = self.env['product.product'].search([('qty_available', '<=', 0), ('type', '=', 'product')])
        print '[RESET] - Ho estratto %s prodotti da disattivare' % len(products_to_deactivate)
        context = {
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
            'mail_notrack': True,
            'skip_notification_mail': True,
            'skip_products_log_tracking': True
        }
        products_to_deactivate.with_context(context).write({'sale_ok': False, 'active': False})
        print '[RESET] - Ho disattivato %s prodotti' % len(products_to_deactivate)

        # devo riattivare tutti i prodotti che hanno quantità fornitore > 0 così da ripopolare il catalogo.
        print '[RESET] - Estraggo tutte le righe fornitore con avail_qty > 0'
        row_supplierinfo = self.env['product.supplierinfo'].search([('avail_qty', '>', 0)])
        print '[RESET] - Ho estratto %s righe fornitore con avail_qty > 0' % len(row_supplierinfo)

        # riaccendo i prodotti con qta fornitore > 0
        print '[RESET] - Riattivo i prodotti con quantità fornitore > 0'
        count = 0
        for row in row_supplierinfo:
            if not row.product_id.active:
                row.product_id.with_context(context).write({'sale_ok': True, 'active': True})
                count += 1
        print '[RESET] - Ho riattivato %s prodotti con quantità fornitore > 0' % count

        print '[RESET] - Azzero tutte le quantità fornitore in attesa di octopus'
        row_supplierinfo.with_context(context).write({'avail_qty': 0})
        print '[RESET] - Ho azzerato la quantità di %s righe fornitore' % len(row_supplierinfo)

        print '[RESET] - Estraggo tutti i prodotti attivi con qty_available > 0 e metto i limiti'
        active_products = self.env['product.product'].search([('qty_available', '>', 0), ('type', '=', 'product')])
        active_products.with_context(context).write({'qty_limit': 0, 'limit_action': 'no_purchasable'})
        print '[RESET] - Ho messo a %s prodotti attivi con qty_available > 0 Limite 0 e non vendibile' % len(active_products)

        print '[RESET] - Estraggo i prodotti in prenotazione e li riattivo'
        date_products = self.env['product.product'].search([('out_date', '>=', datetime.date.today()), ('active', '=', False)])
        count = 0
        for prod in date_products:
            prod.with_context(context).active = True
            if prod.qty_available_now > prod.qty_limit:
                prod.with_context(context).sale_ok = True
                count += 1
        print '[RESET] - Ho messo in vendita %s su %s prodotti riattivati in prenotazione' % (count, len(date_products))
        end = time.time()
        print(end - start)
        return True
