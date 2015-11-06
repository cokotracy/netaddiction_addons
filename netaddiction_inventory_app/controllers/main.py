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
        return request.render(
            'netaddiction_inventory_app.index',
            )

    @http.route('/inventory/app/barcode/', type='http', auth='user', csrf=False)
    def get_barcode(self, debug=False, **k):
        products = request.env['product.product']
        barcode = str(request.params['barcode'])
        result = products.get_picking_order(barcode)
        if isinstance(result,Error):
            return request.render(
                'netaddiction_inventory_app.error',
                {'error' : result}
                )

        return request.render(
            'netaddiction_inventory_app.barcode',
            {'products' : result}
            )
