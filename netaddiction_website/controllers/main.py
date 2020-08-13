from odoo import http
from odoo.http import request

class WebsiteSale(http.Controller):

    @http.route('/netaddiction_website/mostly_sold', type="json", auth='public', website=True)
    def products_mostly_sold(self, **kwargs):
        return self._get_products_mostly_sold()

    def _get_products_mostly_sold():
        #fetch code
