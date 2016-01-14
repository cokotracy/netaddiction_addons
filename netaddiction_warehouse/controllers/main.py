# -*- coding: utf-8 -*-
import logging
import werkzeug.utils

from openerp import http
from openerp.http import request

_logger = logging.getLogger(__name__)

from ..models.error import Error

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

    @http.route('/inventory/app/search/result_from_product', type='http', auth='user', csrf=False)
    def get_allocation(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        products = request.env['product.product']
        barcode = str(request.params['barcode']).strip()
        result = products.get_allocation(barcode)
        product = products.search([('barcode','=',barcode)])

        if isinstance(result,Error):
            return request.render(
                'netaddiction_warehouse.error',
                {'error' : result,'user' : user, 
                'top_back_url' : '/inventory/app/search/from_product'}
                )

        return request.render(
            'netaddiction_warehouse.result_from_product',
            {'user' : user, 'allocations' : result,'product' : product,
            'top_back_url' : '/inventory/app/search/from_product'}
            )

    @http.route('/inventory/app/search/result_from_shelf', type='http', auth='user', csrf=False)
    def get_products_from_alloc(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        barcode = str(request.params['barcode']).strip()
        
        loc_line = request.env['netaddiction.wh.locations.line']
        result = loc_line.get_products(barcode)

        shelf = request.env['netaddiction.wh.locations'].search([('barcode','=',barcode)])


        if isinstance(result,Error):
            return request.render(
                'netaddiction_warehouse.error',
                {'error' : result,'user' : user, 
                'top_back_url' : '/inventory/app/search/from_shelf'}
                )

        return request.render(
            'netaddiction_warehouse.result_from_shelf',
            {'user' : user, 'allocations' : result, 'shelf' : shelf,
            'top_back_url' : '/inventory/app/search/from_shelf'}
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

    @http.route('/inventory/app/allocation/barcode', type='http', auth='user')
    def allocation_result(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])
       
        products = request.env['product.product']
        barcode = str(request.params['barcode']).strip()
        result = products.get_allocation(barcode)
        product = products.search([('barcode','=',barcode)])

        if isinstance(result,Error):
            return request.render(
                'netaddiction_warehouse.error',
                {'error' : result,'user' : user, 
                'top_back_url' : '/inventory/app/allocation'}
                )

        return request.render(
            'netaddiction_warehouse.result_barcode',
            {'user' : user, 'allocations' : result,'product' : product,
            'top_back_url' : '/inventory/app/allocation'}
            )

    @http.route('/inventory/app/allocation/new_shelf', type='http', auth='user')
    def new_shelf(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        qta = int(request.params['alloc_qty'])
        new_shelf = str(request.params['new_shelf']).strip()
        old_line_id = str(request.params['old_line_id']).strip()

        new_location = request.env['netaddiction.wh.locations'].check_barcode(new_shelf)
        if isinstance(new_location,Error):
            return request.render(
                'netaddiction_warehouse.error',
                {'error' : new_location,'user' : user, 
                'top_back_url' : '/inventory/app/allocation'}
                )

        old = request.env['netaddiction.wh.locations.line'].search([('id','=',old_line_id)])

        diff = old.qty - qta
        if diff < 0:
            err = Error()
            err.set_error_msg("Non puoi scaricare una quantità maggiore di quella allocata")
            return request.render(
                'netaddiction_warehouse.error',
                {'error' : err,'user' : user, 
                'top_back_url' : '/inventory/app/allocation'}
                )
        
        product = old.product_id

        request.env['netaddiction.wh.locations.line'].allocate(old.product_id.id,qta,new_location.id)

        decrement = old.decrease(qta)

        result = request.env['product.product'].get_allocation(product.barcode)
        
        if isinstance(result,Error):
            return request.render(
                'netaddiction_warehouse.error',
                {'error' : result,'user' : user, 
                'top_back_url' : '/inventory/app/allocation'}
                )


        return request.render(
            'netaddiction_warehouse.result_barcode',
            {'user' : user, 'allocations' : result,'product' : product,
            'top_back_url' : '/inventory/app/allocation', 'message_done' : 'Allocazione Completata'}
            )

    #########
    #PICK UP#
    #########
    @http.route('/inventory/app/pick_up', type='http', auth='user')
    def index_pick_up(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id','=',uid)])

        #prendo tutte le liste di prelievo in stato draft
        waves = request.env['stock.picking.wave'].search([('state','=','draft')])

        return request.render(
            'netaddiction_warehouse.pick_up_index', 
            {
                'waves' : waves,
                'user' : user,
                'top_back_url' : '/inventory/app/',
            }
            )