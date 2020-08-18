from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request



class WebsiteSale(WebsiteSale):

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

    # @http.route('/shop/immediate_available', type="http", auth='public', website=True)
    # def immediate_available(self):
    #     self._get_search_domain();
    # def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
    #     # obj = request.env['']
    #     import pdb;pdb.set_trace()