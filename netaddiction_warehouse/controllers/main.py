# -*- coding: utf-8 -*-
import logging
import werkzeug.utils

from openerp import http
from openerp.http import request
from openerp.http import Response 
from openerp.http import JsonRequest

_logger = logging.getLogger(__name__)

from ..models.error import Error

from collections import defaultdict

class InventoryApp(http.Controller):

    @http.route('/inventory/app', type='http', auth='user')
    def index(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session

        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/inventory/app')

        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        waves = request.env['stock.picking.wave'].search([('state','=','draft'),('in_exit','=',False),('reverse_supplier','=',False)])
        waves_in_progress = request.env['stock.picking.wave'].search([('state','=','in_progress'),('in_exit','=',False),('reverse_supplier','=',False)])

        waves_reverse = request.env['stock.picking.wave'].search([('state','=','draft'),('reverse_supplier','=',True)])
        waves_in_progress_reverse = request.env['stock.picking.wave'].search([('state','=','in_progress'),('reverse_supplier','=',True)])

        return request.render(
            'netaddiction_warehouse.index',
            {
                'user' : user ,
                'count_waves_draft' : len(waves),
                'count_waves_progress' : len(waves_in_progress),
                'count_waves_reverse' : len(waves_reverse),
                'count_waves_progress_reverse' : len(waves_in_progress_reverse)
            }
            )

    #########
    #RICERCA#
    #########

    @http.route('/inventory/app/search/from_product', type='http', auth='user')
    def searching(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])
        return request.render(
            'netaddiction_warehouse.search_from_product',
            {'user' : user ,'top_back_url' : '/inventory/app'}
            )

    @http.route('/inventory/app/search/from_shelf', type='http', auth='user')
    def searching_shelf(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])
        return request.render(
            'netaddiction_warehouse.search_from_shelf',
            {'user' : user ,'top_back_url' : '/inventory/app'}
            )
        
    #############
    #ALLOCAZIONE#
    #############

    @http.route('/inventory/app/allocation', type='http', auth='user')
    def allocation(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])
        return request.render(
            'netaddiction_warehouse.allocation',
            {'user' : user ,'top_back_url' : '/inventory/app'}
            )
          

    #########
    #PICK UP#
    #########
    @http.route('/inventory/app/pick_up', type='http', auth='user')
    def index_pick_up(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        waves = request.env['stock.picking.wave'].search([('state','in',['draft','in_progress']),('in_exit','=',False),('reverse_supplier','=',False)]).sorted(key=lambda r: r.id)
        
        return request.render(
            'netaddiction_warehouse.pick_up_index', 
            {
                'waves' : waves,
                'user' : user,
                'top_back_url' : '/inventory/app/',
            }
            )

    @http.route('/inventory/app/pick_up_reverse', type='http', auth='user')
    def index_pick_up_reverse(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        waves = request.env['stock.picking.wave'].search([('state','in',['draft','in_progress']),('reverse_supplier','=',True)]).sorted(key=lambda r: r.id)

        return request.render(
            'netaddiction_warehouse.pick_up_reverse_index', 
            {
                'waves' : waves,
                'user' : user,
                'top_back_url' : '/inventory/app/',
            }
            )

    @http.route('/inventory/app/pick_up/<wave_id>', type='http', auth='user')
    def wave_pick_up(self, wave_id, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        wave = request.env['stock.picking.wave'].search([('id','=',wave_id),
            ('picking_ids.pack_operation_product_ids.state','in',['assigned','partially_available'])]
            )

        if wave.state == 'draft':
            wave.write({'state': 'in_progress'})

        if wave.reverse_supplier == True:
            is_reverse = True
        else:
            is_reverse = False

        #prendo i prodotti raggruppati
        products = wave.get_product_list()
        #assegno i ripiani
        datas = defaultdict(list)
        for product,qtys in products.items():
            shelf = product.get_shelf_to_pick(qtys['product_qty'] - qtys['qty_done'])
            for s,q in shelf.items():
                text = {'qta':q,'name':product.display_name, 'pid' : product.id, 'barcode':product.barcode, 'shelf_id':s.id}
                datas[s.name].append(text)
            if qtys['qty_scraped']>0:
                text = {'qta':int(qtys['qty_scraped']),'name':product.display_name, 'pid' : product.id, 'barcode':product.barcode, 'shelf_id':qtys['scraped_wh']}
                datas['Magazzino Difettati'].append(text)
            

        sorted_list = sorted(datas.items(), key = lambda (k,v): k)

        pre = []
        middle = []
        for s in sorted_list:
            sp = s[0].split('/')
            pre.append(sp[0])
            middle.append(int(sp[1]))
        pre = list(set(pre))
        middle = list(set(middle))
        pre.sort()
        middle.sort()
        
        v = {}
        for s in sorted_list:
            sp = s[0].split('/')
            pind = pre.index(sp[0])
            mind = middle.index(int(sp[1]))
            if pind not in v.keys():
                v[pind] = {}
            if mind not in v[pind].keys():
                v[pind][mind] = [s]
            else:
                v[pind][mind].append(s)

        result = []
        for i in v:
            for t in v[i]:
                result += v[i][t]

        return request.render(
            'netaddiction_warehouse.wave', 
            {
                'user' : user,
                'top_back_url' : '/inventory/app/pick_up',
                'lists' : result,
                'top_title' : wave.display_name,
                'is_reverse' : is_reverse
            }
            )

