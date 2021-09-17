# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale


class NetaddictionWebsiteSale(WebsiteSale):

    @route('/sale/netaddiction/website/data',
           type='json', auth="public", website=True)
    def save_netaddiction_so_data(self, **post):
        # Retrieve the sale order
        so_id = post.get('order_id')
        access_token = post.get('access_token')
        if so_id:
            env = request.env['sale.order'].sudo()
            domain = [('id', '=', so_id)]
            if access_token:
                domain.append(('access_token', '=', access_token))
            order = env.search(domain, limit=1)
        else:
            order = request.website.sale_get_order()
        order.note = post.get('note', '')
        return True

    @route()
    def cart_update_json(self, product_id, line_id=None, add_qty=None,
                         set_qty=None, display=True):
        value = super().cart_update_json(
            product_id, line_id, add_qty, set_qty, display)
        if value and \
                value.get('order_limit', 0) and \
                value.get('cart_quantity', 0) in value and \
                value['cart_quantity'] > value['order_limit']:
            del value['cart_quantity']
        return value
