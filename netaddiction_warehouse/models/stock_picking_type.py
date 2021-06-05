import time

from odoo import models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def _compute_picking_count(self):
        """
        Override della funzione di conteggio di default di odoo.
        In questa versione se l'ordine di vendita risulta nello stato 'DONE'
        non appare gli ordini da dover "processare" e mettere in lista prelievo
        """
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                [('state', 'not in', ('done', 'cancel')),
                 ('sale_id.state', '!=', 'done'),  # Ignoriamo i picking di SO completati
                 ('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)
        for record in self:
            record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
            record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0

    # Per compatibilità con v9.0
    # Rationale: su v9.0, la compute ``_compute_picking_count`` si chiamava
    # ``_get_picking_count``. Ma questo modulo ridefiniva l'attributo
    # ``compute`` dei field calcolati da quella compute con un nuovo metodo
    # ``_get_picking_out_count``. Siccome non abbiamo certezza che questo
    # metodo non sia richiamato altrove, pur essendo l'override di un metodo
    # deprecato e rinominato, per compatibilità lo ridefiniamo così
    _get_picking_out_count = _compute_picking_count
