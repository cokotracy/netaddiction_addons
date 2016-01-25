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
        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        waves = request.env['stock.picking.wave'].search([('state','=','draft')])

        return request.render(
            'netaddiction_warehouse.index',
            {
                'user' : user ,
                'count_waves' : len(waves),
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

     #LINE DI DEMARCAZIONE: DA QUI IN POI E' ROBA VECCHIA DA CORREGGERE#
          

    #########
    #PICK UP#
    #########
    @http.route('/inventory/app/pick_up', type='http', auth='user')
    def index_pick_up(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        waves = request.env['stock.picking.wave'].search([('state','=','draft')]).sorted(key=lambda r: r.id)

        return request.render(
            'netaddiction_warehouse.pick_up_index', 
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

        #prendo i prodotti raggruppati
        products = wave.get_product_list()

        #assegno i ripiani
        datas = defaultdict(list)
        for product,qtys in products.items():
            shelf = product.get_shelf_to_pick(qtys['product_qty'] - qtys['qty_done'])
            for s,q in shelf.items():
                text = {'qta':q,'name':product.display_name}
                datas[s.name].append(text)

        sorted_list = sorted(datas.items(), key = lambda (k,v): k)

        return request.render(
            'netaddiction_warehouse.wave', 
            {
                'user' : user,
                'top_back_url' : '/inventory/app/pick_up',
                'lists' : sorted_list,
                'top_title' : wave.display_name,
            }
            )

    ##############
    #JSON REQUEST#
    ##############

    @http.route('/inventory/app/pick_product', type="json", auth="user", csrf=False)
    def pick_product(self):
        data = request.jsonrequest
        barcode = data['barcode']
        product = request.env['product.product']._get_product_from_barcode(barcode)
        result = ''

        print request.context
        print request.session
        print request.params
        if isinstance(product,Error):
            result = product.get_error_msg()
            return {
                'error' : 1,
                'result': result
            }

        result = request.env['stock.picking.wave'].is_in_wave(wave_id,product.id)
