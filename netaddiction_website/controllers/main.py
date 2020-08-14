from odoo import http
from odoo.http import request

class WebsiteSale(http.Controller):

    @http.route('/netaddiction_website/mostly_sold', type="json", auth='public', website=True)
    def products_mostly_sold(self, **kwargs):
        return self._get_products_mostly_sold()

    def _get_products_mostly_sold(self):

        # excluded_products = request.website.sale_get_order().mapped('order_line.product_id.id')
        # products = request.env['product.product'].sudo().read_group(
        #         [],
        #         ['product_id', 'sales_count:max'], ['product_id'], limit=12, orderby='visit_datetime DESC')
        # products = request.env['product.product'].sudo().read_group(
        #         [],
        #         ['id', 'sales_count'], ['id'], limit=12, orderby='sales_count')
        res = {'products': []}
        products = request.env['product.template'].search([])
        for product in products:
            res_product = product.read(['id', 'name', 'website_url'])[0]
            res['products'].append(res_product)
        return res