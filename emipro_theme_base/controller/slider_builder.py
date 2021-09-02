from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from datetime import timedelta
import datetime
from odoo.http import request
from odoo import http, _
from odoo.tools.safe_eval import safe_eval


class SliderBuilder(WebsiteSale):

    # Render the product list
    @http.route(['/get-product-list'], type='json', auth="public", website=True)
    def get_product_listing(self, name=False, **kwargs):
        products = filters = error = error_msg = False
        limit = kwargs.get('limit')
        if name:
            if name == 'new-arrival':
                products = self.new_arrival_products(20)
                error = True if not products else False
            elif name == 'best-seller':
                products = self.best_seller_products(20)
                error = True if not products else False
            elif name == 'product-discount':
                products = self.discounted_products('product', 20)
                error = True if not products else False
            elif name == 'product-category-discount':
                products = self.discounted_products('category', request.website.category_check().ids,
                                                    discount_policy='product', limit=20)
                error = True if not products else False
            elif name == 'custom-domain':
                filters = request.env['slider.filter'].sudo().search(
                    [('website_published', '=', True), ('filter_domain', '!=', False)])
                error = True if not filters else False
            elif name == 'manual-configuration':
                products = request.env['product.template'].sudo().search([], limit=2)
                error = True if not products else False
        if error:
            error_msg = _("ERROR MESSAGE WILL BE DISPLAYED HERE")
        response = http.Response(template='emipro_theme_base.product_display_prod_template',
                                 qcontext={'name': name, 'limit': limit, 'products': products, 'filters': filters,
                                           'error': error, 'error_msg': error_msg})
        return {'template_data': response.render(), 'error': error, 'error_msg': error_msg}

    # Render the the selected products while edit the manual configuration slider
    @http.route('/get-products-of-slider', type='json', auth='public', website=True)
    def get_products_of_slider(self, **kw):
        product_ids = kw.get('item_ids')
        if product_ids:
            products = request.env['product.template'].browse(product_ids).filtered(
                lambda r: r.exists() and r.sale_ok and r.website_published and r.website_id.id in (
                False, request.website.id) and r.type in ['product', 'consu'])
            response = http.Response(template='emipro_theme_base.edit_product_template',
                                     qcontext={'products': products})
            return response.render()

    @http.route('/load-more-category-brand', type='json', auth='public', website=True)
    def load_more_category_brand(self, **kw):
        name = kw.get('name')
        loaded_items = kw.get('loaded_items')
        loaded_items = int(loaded_items) if loaded_items else False
        item_ids = kw.get('item_ids', False)
        item_ids = [int(i) for i in item_ids.split(',')] if item_ids and type(item_ids) == str else [int(i) for i in
                                                                                                     item_ids] if item_ids else False
        response = False
        items, items_count = self.get_category_brand(name=name, ) if loaded_items and name else False
        items = (items - items.filtered(lambda r: r.id not in item_ids)) + items.filtered(
            lambda r: r.id not in item_ids) if item_ids else items
        items = items[loaded_items:loaded_items + 20]
        if items:
            tmplt = request.env['ir.ui.view'].sudo().search(
                [('key', '=', 'emipro_theme_base.brand_category_configure_template')])
            if tmplt:
                response = http.Response(template='emipro_theme_base.list_items',
                                         qcontext={'items': items, 'name': name})
        return {'response': response.render() if response else False, 'items_count': items_count,
                'loaded_items': loaded_items + len(items) if items else loaded_items if loaded_items else 20, }

    # Render Category or Brand and it's count
    def get_category_brand(self, name, item_ids=False):
        items = False
        items_count = False
        domain = []
        limit = len(item_ids) if item_ids else 20
        if name == 'category-slider':
            domain = [('website_id', 'in', [False, request.website.id]), ('image_1920', '!=', False),
                      ('id', 'in', item_ids)] if item_ids else [('website_id', 'in', [False, request.website.id]),
                                                                ('image_1920', '!=', False)]
            items = request.env['product.public.category'].sudo().search(domain, order='id desc')
            items_count = request.env['product.public.category'].sudo().search_count(
                [('website_id', 'in', [False, request.website.id]), ('image_1920', '!=', False)])
        else:
            domain = [('website_id', 'in', [False, request.website.id]), ('logo', '!=', False), ('id', 'in', item_ids),
                      ('website_published', '=', True)] if item_ids else [('website_published', '=', True), (
            'website_id', 'in', [False, request.website.id]), ('logo', '!=', False)]
            items = request.env['product.brand.ept'].sudo().search(domain, order='id desc')
            items_count = request.env['product.brand.ept'].sudo().search_count(
                [('website_published', '=', True), ('website_id', 'in', [False, request.website.id]),
                 ('logo', '!=', False)])
        return items, items_count

    # Render Slider Popup
    @http.route('/get-slider-builder-popup', type='json', auth='public', website=True)
    def get_brand_category_template(self, **kw):
        name = kw.get('name')
        exclude = kw.get('exclude', False)
        limit = kw.get('limit')
        slider_type = 'category'
        items = False
        item_ids = kw.get('item_ids', False)
        item_ids = [int(i) for i in item_ids.split(',')] if item_ids and type(item_ids) == str else [int(i) for i in
                                                                                                     item_ids] if item_ids else False

        if name in ['category-slider', 'brand-slider']:
            items, items_count = self.get_category_brand(name, item_ids=item_ids)
            items = items[:20]
            loaded_items = len(item_ids) if item_ids else 20
            slider_type = 'category' if name == 'category-slider' else 'brand'
            tmplt = request.env['ir.ui.view'].sudo().search(
                [('key', '=', 'emipro_theme_base.brand_category_configure_template')])
            styles = request.env['slider.styles'].search(
                [('slider_type', '=', slider_type), ('style_template_key', '!=', False)])
            if tmplt:
                response = http.Response(template='emipro_theme_base.brand_category_configure_template',
                                         qcontext={'name': name, 'items': items, 'items_count': items_count,
                                                   'limit': limit, 'styles': styles, 'exclude': exclude,
                                                   'loaded_items': loaded_items,
                                                   'available_slider_style': list(set(styles.mapped('slider_style')))})
                return response.render()
        else:
            tmplt = request.env['ir.ui.view'].sudo().search(
                [('key', '=', 'emipro_theme_base.product_configure_template')])
            filters = request.env['slider.filter'].sudo().search(
                [('website_published', '=', True), ('filter_domain', '!=', False)])
            styles = request.env['slider.styles'].search(
                [('slider_type', '=', 'product'), ('style_template_key', '!=', False)])
            if tmplt:
                response = http.Response(template='emipro_theme_base.product_configure_template',
                                         qcontext={'name': name, 'filters': filters, 'styles': styles, 'exclude': exclude,
                                                   'available_slider_style': list(set(styles.mapped('slider_style')))})
                return response.render()


    # Render Suggested Product
    @http.route('/get-suggested-products', type='json', auth='public', website=True)
    def get_suggested_products(self, **kw):
        key = kw.get('key')
        exclude_products = kw.get('exclude_products')
        website_domain = request.website.website_domain()
        products = request.env['product.template'].search(
            [('id', 'not in', exclude_products), ('sale_ok', '=', True), ('name', 'ilike', key),
             ('type', 'in', ['product', 'consu']), ('website_published', '=', True)] + website_domain,
            limit=10)
        tmplt = request.env['ir.ui.view'].sudo().search(
            [('key', '=', 'emipro_theme_base.suggested_products')])
        if tmplt:
            response = http.Response(template='emipro_theme_base.suggested_products', qcontext={'products': products})
            return response.render()

    # Render the category And brand slider
    @http.route(['/slider/category-brand-render'], type='json', auth="public", website=True)
    def category_brand_render(self, **kwargs):
        item_ids = kwargs.get('item_ids', False)
        name = kwargs.get('name', False)
        item_ids = [int(i) for i in item_ids.split(',')] if item_ids and type(item_ids) == str else [int(i) for i in
                                                                                                     item_ids] if item_ids else False
        limit = kwargs.get('limit', False)
        limit = int(limit) if limit else 10
        style = kwargs.get('style', False)
        style = int(style) if style else False
        sort_by = kwargs.get('sort_by', 'name asc')
        display_product_count = True if kwargs.get('product_count') and kwargs.get('product_count') == '1' else False

        items = False
        if item_ids and name:
            slider_style = request.env['slider.styles'].sudo().browse(style).filtered(
                lambda r: r.exists())
            if name == 'brand-slider':
                items = request.env['product.brand.ept'].search([('id', 'in', item_ids)], limit=limit,
                                                                order=sort_by).filtered(
                    lambda r: r.exists() and r.website_id.id in [False,
                                                                 request.website.id] and r.website_published and r.logo)
            else:
                items = request.env['product.public.category'].search([('id', 'in', item_ids)], limit=limit,
                                                                      order=sort_by).filtered(
                    lambda r: r.exists() and r.image_1920 and r.website_id.id in [False, request.website.id])
            if items and slider_style:
                vals = {"items": items, 'display_product_count': display_product_count}
                if request.env['ir.ui.view'].sudo().search(
                        [('key', '=', request.website.sudo().theme_id.name + '.' + slider_style.style_template_key)]):
                    response = http.Response(
                        template=request.website.sudo().theme_id.name + '.' + slider_style.style_template_key,
                        qcontext=vals)
                    return response.render()
        if request.env['ir.ui.view'].sudo().search(
                [('key', '=', request.website.sudo().theme_id.name + '.' + 'slider_error_message')]):
            response = http.Response(template=request.website.sudo().theme_id.name + '.' + 'slider_error_message')
            return response.render()

    # Render The Product Slider
    @http.route(['/slider/render'], type='json', auth="public", website=True)
    def slider_data(self, **kwargs):
        item_ids = kwargs.get('item_ids', False)
        item_ids = [int(i) for i in item_ids.split(',')] if item_ids and type(item_ids) == str else [int(i) for i in
                                                                                                     item_ids] if item_ids else False
        selected_ui_options = kwargs.get('ui_options', False)
        selected_ui_options = [i for i in selected_ui_options.split(',')] if selected_ui_options and type(
            selected_ui_options) == str else [i for i in selected_ui_options] if selected_ui_options else False
        slider_style_template = kwargs.get('style', False)
        slider_style_template = int(slider_style_template) if slider_style_template else False
        name = kwargs.get('name', False)
        discount_policy = kwargs.get('discount_policy', False)
        limit = kwargs.get('limit', False)
        limit = int(limit) if limit else 10
        sort_by = kwargs.get('sort_by', 'name asc')
        products = []

        if name and slider_style_template:
            slider_style = request.env['slider.styles'].sudo().browse(slider_style_template).filtered(
                lambda r: r.exists())
            vals = {
                'option': selected_ui_options or [],
            }
            if name == 'manual-configuration' and item_ids:
                products = request.env['product.template'].sudo().browse(item_ids).filtered(lambda r: r.exists())
                products = products.sudo().filtered(lambda r: r.sale_ok and r.website_published and r.website_id.id in (
                    False, request.website.id) and r.type in ['product', 'consu'])[:limit]
            elif name == 'new-arrival':
                products = self.new_arrival_products(limit)
            elif name == 'custom-domain':
                products = self.custom_domain_products(item_ids, limit, sort_by)
            elif name == 'best-seller':
                products = self.best_seller_products(limit)
            elif name == 'product-discount':
                products = self.discounted_products('product', limit=limit)
            elif name == 'product-category-discount' and item_ids:
                products = self.discounted_products('category', item_ids, discount_policy, limit)
            if products and slider_style:
                vals['filter_data'] = products[:limit]
                if request.env['ir.ui.view'].sudo().search(
                        [('key', '=', request.website.sudo().theme_id.name + '.' + slider_style.style_template_key)]):
                    response = http.Response(
                        template=request.website.sudo().theme_id.name + '.' + slider_style.style_template_key,
                        qcontext=vals)
                    return response.render()

        if request.env['ir.ui.view'].sudo().search(
                [('key', '=', request.website.sudo().theme_id.name + '.' + 'slider_error_message')]):
            response = http.Response(template=request.website.sudo().theme_id.name + '.' + 'slider_error_message')
            return response.render()

    # Render the custom domain products
    def custom_domain_products(self, filter_id, limit=20, sort_by='name asc'):
        filter = False
        if filter_id:
            filter = request.env['slider.filter'].sudo().browse(filter_id[0]).filtered(lambda r: r.exists())
        if filter and filter.website_published:
            domain = safe_eval(filter.filter_domain)
            domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                       ('website_published', '=', True), ('type', 'in', ['product', 'consu']), ('sale_ok', '=', True)]
            return request.env['product.template'].sudo().search(domain, limit=limit, order=sort_by)
        return False

    # Render the new arrival products
    def new_arrival_products(self, limit=10):
        domain = request.website.sale_product_domain()
        domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                   ('website_published', '=', True), ('type', 'in', ['product', 'consu'])]
        return request.env['product.template'].sudo().search(domain, limit=limit, order='id desc')

    # Render the best seller products
    def best_seller_products(self, limit=10):
        website_id = request.website.id
        request.env.cr.execute("""select * from sale_report where website_id=%s AND state in ('sale','done') AND date BETWEEN %s and %s
                                                """,
                               (website_id, datetime.datetime.today() - timedelta(30), datetime.datetime.today()))
        sale_report_ids = [x[0] for x in request.env.cr.fetchall()]
        products = request.env['sale.report'].sudo().browse(sale_report_ids).filtered(lambda r: r.exists()).mapped(
            'product_tmpl_id')
        products = products.filtered(lambda r: r.website_published and r.sale_ok and r.website_id.id in (
            False, website_id) and r.type != 'service')[:limit]
        return products

    # Return Category product or category discount product
    def discounted_products(self, applied_on=False, category_ids=False, discount_policy=False, limit=10):
        price_list = request.website.get_current_pricelist()
        pl_items = price_list.item_ids.filtered(lambda r: r.applied_on == '1_product' and (
                (not r.date_start or r.date_start <= datetime.datetime.today()) and (
                not r.date_end or r.date_end > datetime.datetime.today())))
        if applied_on == 'product':
            return pl_items.mapped('product_tmpl_id').filtered(
                lambda r: r.sale_ok and r.website_published and r.website_id.id in (
                False, request.website.id) and r.type in ['product', 'consu'])[:limit]
        elif category_ids and applied_on == 'category' and discount_policy == 'discounts':
            return pl_items.mapped('product_tmpl_id').filtered(
                lambda r: r.sale_ok and r.website_published and r.website_id.id in (
                False, request.website.id) and r.type in ['product', 'consu'] and [i for i in category_ids if
                                                                                   i in r.public_categ_ids.ids])[:limit]
        else:
            domain = request.website.sale_product_domain()
            domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                       ('website_published', '=', True), ('public_categ_ids', 'in', category_ids),
                       ('type', 'in', ['product', 'consu'])]
            return request.env['product.template'].sudo().search(domain, limit=limit)
        return False
