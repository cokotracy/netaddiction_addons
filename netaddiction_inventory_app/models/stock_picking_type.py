# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date, datetime
from dateutil import relativedelta
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from error import Error

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
            data = obj.read_group( domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = dict(map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
            for tid in self.ids:
                self.update({field:count.get(tid, 0)})
                
