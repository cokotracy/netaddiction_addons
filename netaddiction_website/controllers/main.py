from odoo import http
from odoo.http import request

class WebsiteSale(http.Controller):

    @http.route('/netaddiction_website/mostly_sold', type="json", auth='public', website=True)
    def products_mostly_sold(self, **kwargs):
        return self._get_products_mostly_sold()

    def _get_products_mostly_sold(self):
        res = {'products': []}
        products = request.env['product.template'].search([])
        for product in products:
            res_product = product.read(['id', 'name', 'website_url'])[0]
            res['products'].append(res_product)
        return res