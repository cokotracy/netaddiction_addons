# -*- coding: utf-8 -*-
import logging

from openerp import http
from openerp.http import request
from collections import defaultdict

_logger = logging.getLogger(__name__)

class GrouponApp(http.Controller):

    @http.route('/inventory/app/groupon_pick_up', type='http', auth='user')
    def groupon_index_pick_up(self, debug=False, **k):
        uid = request.uid
        user = request.env['res.users'].search([('id', '=', uid)])

        waves = request.env['groupon.pickup.wave'].search([('state', 'in', ['draft'])]).sorted(key=lambda r: r.id)

        return request.render(
            'netaddiction_groupon.list_wave',
            {
                'waves': waves,
                'user': user,
                'top_back_url': '/inventory/app/', })

    @http.route('/inventory/app/groupon_pick_up/<wave_id>', type='http', auth='user')
    def groupon_wave_pick_up(self, wave_id, debug=False, **k):
        uid = request.uid
        user = request.env['res.users'].search([('id', '=', uid)])

        wave = request.env['groupon.pickup.wave'].search([('id', '=', int(wave_id))])

        if len(wave) == 0:
            return request.render(
                'netaddiction_groupon.error_wave',
                {
                    'user': user,
                    'error': 'LISTA INESISTENTE',
                    'top_back_url': '/inventory/app/groupon_pick_up', })

        if wave.state != 'draft':
            return request.render(
                'netaddiction_groupon.error_wave',
                {
                    'user': user,
                    'error': 'LISTA COMPLETATA',
                    'top_back_url': '/inventory/app/groupon_pick_up', })

        products = wave.get_list_products()

        datas = defaultdict(list)
        for product, qtys in products.items():
            shelf = wave.get_groupon_shelf_to_pick(product, qtys['product_qty'] - qtys['qty_done'])
            for s, q in shelf.items():
                text = {'qta': q, 'name': product.display_name, 'pid': product.id, 'barcode': product.barcode, 'shelf_id': s.id}
                datas[s.name].append(text)

        sorted_list = sorted(datas.items(), key=lambda (k, v): k)

        return request.render(
            'netaddiction_groupon.groupon_wave',
            {
                'user': user,
                'top_back_url': '/inventory/app/groupon_pick_up',
                'lists': sorted_list,
                'top_title': wave.name, })
