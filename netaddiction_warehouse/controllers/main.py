import logging

from collections import defaultdict

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class InventoryApp(http.Controller):

    @http.route('/inventory/app', type='http', auth='user')
    def index(self, debug=False, **k):
        if not (request.uid and request.session.uid):
            return http.local_redirect('/web/login?redirect=/inventory/app')

        # prendo tutte le liste di prelievo in stato draft
        batch_obj = request.env['stock.picking.batch']
        count_batchs_draft = batch_obj.search_count(
            [('state', '=', 'draft'),
             ('in_exit', '=', False),
             ('reverse_supplier', '=', False)]
        )
        count_batchs_progress = batch_obj.search_count(
            [('state', '=', 'in_progress'),
             ('in_exit', '=', False),
             ('reverse_supplier', '=', False)]
        )
        count_batchs_reverse = batch_obj.search_count(
            [('state', '=', 'draft'),
             ('reverse_supplier', '=', True)]
        )
        count_batchs_progress_reverse = batch_obj.search_count(
            [('state', '=', 'in_progress'),
             ('reverse_supplier', '=', True)]
        )

        return request.render(
            'netaddiction_warehouse.index',
            qcontext={
                'user': request.env['res.users'].browse(request.uid),
                'count_batchs_draft': count_batchs_draft,
                'count_batchs_progress': count_batchs_progress,
                'count_batchs_reverse': count_batchs_reverse,
                'count_batchs_progress_reverse': count_batchs_progress_reverse
            }
        )

    ###########
    # RICERCA #
    ###########

    @http.route('/inventory/app/search/from_product', type='http', auth='user')
    def searching(self, debug=False, **k):
        return request.render(
            'netaddiction_warehouse.search_from_product',
            qcontext={
                'user': request.env['res.users'].browse(request.uid),
                'top_back_url': '/inventory/app'
            }
        )

    @http.route('/inventory/app/search/from_shelf', type='http', auth='user')
    def searching_shelf(self, debug=False, **k):
        return request.render(
            'netaddiction_warehouse.search_from_shelf',
            qcontext={
                'user': request.env['res.users'].browse(request.uid),
                'top_back_url': '/inventory/app'
            }
        )

    ###############
    # ALLOCAZIONE #
    ###############

    @http.route('/inventory/app/allocation', type='http', auth='user')
    def allocation(self, debug=False, **k):
        return request.render(
            'netaddiction_warehouse.allocation',
            qcontext={
                'user': request.env['res.users'].browse(request.uid),
                'top_back_url': '/inventory/app'
            }
        )

    ###########
    # PICK UP #
    ###########

    @http.route('/inventory/app/pick_up', type='http', auth='user')
    def index_pick_up(self, debug=False, **k):
        # prendo tutte le liste di prelievo in stato draft
        batchs = request.env['stock.picking.batch'].search(
            [('state', 'in', ['draft', 'in_progress']),
             ('in_exit', '=', False),
             ('reverse_supplier', '=', False)],
            order='id asc'
        )
        return request.render(
            'netaddiction_warehouse.pick_up_index',
            qcontext={
                'batchs': batchs,
                'user': request.env['res.users'].browse(request.uid),
                'top_back_url': '/inventory/app/',
            }
        )

    @http.route('/inventory/app/pick_up_reverse', type='http', auth='user')
    def index_pick_up_reverse(self, debug=False, **k):
        # prendo tutte le liste di prelievo in stato draft
        batchs = request.env['stock.picking.batch'].search(
            [('state', 'in', ['draft', 'in_progress']),
             ('reverse_supplier', '=', True)],
            order='id asc'
        )
        return request.render(
            'netaddiction_warehouse.pick_up_reverse_index',
            qcontext={
                'batchs': batchs,
                'user': request.env['res.users'].browse(request.uid),
                'top_back_url': '/inventory/app/',
            }
        )

    @http.route('/inventory/app/pick_up/<batch_id>', type='http', auth='user')
    def batch_pick_up(self, batch_id, debug=False, **k):
        # prendo tutte le liste di prelievo in stato draft
        batch = request.env['stock.picking.batch'].browse(int(batch_id))

        if batch.state == 'draft':
            batch.write({'state': 'in_progress'})

        is_reverse = batch.reverse_supplier

        # prendo i prodotti raggruppati
        products = batch.get_product_list()
        # assegno i ripiani
        datas = defaultdict(list)
        for product, qtys in list(products.items()):
            shelf = product.get_shelf_to_pick(
                qtys['product_qty'] - qtys['qty_done']
            )
            for s, q in list(shelf.items()):
                text = {'qta': q,
                        'name': product.display_name,
                        'pid': product.id,
                        'barcode': product.barcode,
                        'shelf_id': s.id}
                datas[s.name].append(text)
            if qtys['qty_scraped'] > 0:
                text = {'qta': int(qtys['qty_scraped']),
                        'name': product.display_name,
                        'pid': product.id,
                        'barcode': product.barcode,
                        'shelf_id': qtys['scraped_wh']}
                datas['Magazzino Difettati'].append(text)

        sorted_list = sorted(list(datas.items()), key=lambda k_v: k_v[0])

        # pre = []
        # middle = []
        # for s in sorted_list:
        #     sp = s[0].split('/')
        #     pre.append(sp[0])
        #     middle.append(int(sp[1]))
        # pre = list(set(pre))
        # middle = list(set(middle))
        # pre.sort()
        # middle.sort()
        # 
        # v = {}
        # for s in sorted_list:
        #     sp = s[0].split('/')
        #     pind = pre.index(sp[0])
        #     mind = middle.index(int(sp[1]))
        #     if pind not in v.keys():
        #         v[pind] = {}
        #     if mind not in v[pind].keys():
        #         v[pind][mind] = [s]
        #     else:
        #         v[pind][mind].append(s)

        # result = []
        # for i in v:
        #     for t in v[i]:
        #         result += v[i][t]

        return request.render(
            'netaddiction_warehouse.batch',
            qcontext={
                'user': request.env['res.users'].browse(request.uid),
                'top_back_url': '/inventory/app/pick_up',
                'lists': sorted_list,
                'top_title': batch.display_name,
                'is_reverse': is_reverse
            }
        )
