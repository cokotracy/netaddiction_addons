# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date, datetime
from dateutil import relativedelta
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from error import Error

from collections import defaultdict

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'


    count_picking_ready = fields.Integer(compute="_get_picking_out_count")
    count_picking_draft = fields.Integer(compute="_get_picking_out_count")
    count_picking_waiting = fields.Integer(compute="_get_picking_out_count")
    count_picking_late = fields.Integer(compute="_get_picking_out_count")
    count_picking_backorders = fields.Integer(compute="_get_picking_out_count")
    rate_picking_late = fields.Integer(compute="_get_picking_out_count")
    rate_picking_backorders = fields.Integer(compute="_get_picking_out_count")
    count_picking = fields.Integer(compute="_get_picking_out_count")

    @api.one
    def _get_picking_out_count(self):
        """
        Sostituisce la funziona di conteggio di default di odoo.
        In questa versione se l'ordine di vendita risulta nello stato 'DONE' non appare
        gli ordini da dover "processare" e mettere in lista prelievo
        """
        obj = self.env['stock.picking']
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', 'in', ('assigned', 'partially_available'))],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
            'count_picking_late': [('min_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting', 'partially_available'))],
        }
        result = {}
        for field in domains:
            data = obj.search( domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)])
            count=len(data)
            for pick in data:
                if len(pick.sale_id)>0:
                    if pick.sale_id.state =='done':
                        count = count -1

            for tid in self.ids:
                self.update({field:count})


class StockPickingWave(models.Model):
    _inherit = 'stock.picking.wave'

    @api.multi
    def get_product_list(self):
        """
        ritorna la lista dei prodotti e le quantità da pickuppare
        """
        self.ensure_one()
        qtys = defaultdict(lambda: defaultdict(float))
        products = {}
        for picks in self.picking_ids:
            for pick in picks.pack_operation_product_ids:
                qtys[pick.product_id.barcode]['product_qty'] += pick.product_qty
                qtys[pick.product_id.barcode]['remaining_qty'] += pick.remaining_qty
                qtys[pick.product_id.barcode]['qty_done'] += pick.qty_done
                products[pick.product_id] = qtys[pick.product_id.barcode]

        return products