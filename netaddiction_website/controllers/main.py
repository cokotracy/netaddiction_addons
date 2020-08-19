from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request
from odoo.osv import expression



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

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
        '/shop/immediate_available',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        import pdb;pdb.set_trace()
        # attrib =
        domain = self._get_search_domain(post.get('filter'),category, attrib=None)

        Product = request.env['product.template'].with_context(bin_size=True)
        search_product = Product.search(domain)

        
        return super(WebsiteSale, self).shop(page=page,category=category, attrib=None)

    def _get_search_domain(self,filter, category, attrib):
        domains = [request.website.sale_product_domain()]
        domains.append([('is_published', '=', 'True')])
        return expression.AND(domains)


