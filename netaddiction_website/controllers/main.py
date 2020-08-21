from werkzeug.exceptions import NotFound
from datetime import timedelta, datetime

from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.osv import expression
from odoo.addons.website.controllers.main import QueryURL


class WebsiteSale(WebsiteSale):

    @http.route('/netaddiction_website/mostly_sold', type="json", auth='public', website=True)
    def products_mostly_sold(self, **kwargs):
        return self._get_products_mostly_sold()

    def _get_products_mostly_sold(self):
        """
        Returns list of recently viewed products according to current user
        """
        FieldMonetary = request.env['ir.qweb.field.monetary']
        monetary_options = {
            'display_currency': request.website.get_current_pricelist().currency_id,
        }
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        domain = ['|', '&', ('net_sales_count', '>', 0), ('is_published', '=', True), ('website_id', '=', request.website.id)]
        for product in request.env['product.product'].search(domain, order="net_sales_count desc", limit=10):
            combination_info = product._get_combination_info_variant()
            res_product = product.read(['id', 'name', 'website_url'])[0]
            res_product.update(combination_info)
            res_product['list_price'] = FieldMonetary.value_to_html(res_product['list_price'], monetary_options)
            # price_formate = FieldMonetary.value_to_html(res_product['price'], monetary_options)
            # res_product['price_decimal'] = u'.' + str(res_product['price']).split('.')[1]
            # res_product['price_integer'] = price_formate.replace(res_product['price_decimal'], '')
            res_product['price'] = FieldMonetary.value_to_html(res_product['price'], monetary_options)
            if rating:
                res_product['rating'] = request.env["ir.ui.view"].render_template('website_rating.rating_widget_stars_static', values={
                    'rating_avg': product.rating_avg,
                    'rating_count': product.rating_count,
                })
            res['products'].append(res_product)

        return res

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        #custom code start
        #pass **post to fetch domain value
        domain = self._get_search_domain(search, category, attrib_values, **post)
        #return price_min and price_max to display in slider
        price_min = post.get('price_min', 1)
        price_max = post.get('price_max', 10000)

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)

        search_product = Product.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'price_min': price_min,
            'price_max': price_max,
        }
        if category:
            values['main_object'] = category
        return request.render("netaddiction_website.products", values)

    def _get_search_domain(self, search, category, attrib_values, **post):
        domains = super(WebsiteSale,self)._get_search_domain(search, category, attrib_values)

        #custom code start
        if post.get('filter'):
            domains.append(('qty_available', '>=', 1))
        if post.get('price_max') and post.get('price_min'):
            domains.append(('list_price', '>=', int(post.get('price_min'))))
            domains.append(('list_price', '<=', int(post.get('price_max'))))
        return domains

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        if not product.can_access_from_current_website():
            raise NotFound()
        return request.render("netaddiction_website.product", self._prepare_product_values(product, category, search, **kwargs))


    def _prepare_product_values(self, product, category, search, **kwargs):
        values = super(WebsiteSale, self)._prepare_product_values(product, category, search, **kwargs)

        #custom code starts
        #get current date and add with estimate date addon for the product
        est_date_addon = product.read(['est_date_addon'])[0]['est_date_addon']
        current_date = str(datetime.now().date()).replace('-','/')
        date = datetime.strptime(current_date, "%Y/%m/%d")
        estimate_date = datetime.strftime((date + timedelta(days=est_date_addon)), "%Y/%m/%d")
        values.update({'estimate_date': estimate_date})
        return values
