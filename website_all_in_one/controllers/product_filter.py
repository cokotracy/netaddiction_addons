# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# import json
# import logging
# from werkzeug.exceptions import Forbidden, NotFound
# from operator import itemgetter

# from odoo import fields, http, tools, _
# from odoo.http import request
# from odoo.addons.base.models.ir_qweb_fields import nl2br
# from odoo.addons.http_routing.models.ir_http import slug
# from odoo.addons.payment.controllers.portal import PaymentProcessing
# from odoo.addons.website.controllers.main import QueryURL
# from odoo.tools import groupby as groupbyelem
# from odoo.exceptions import ValidationError
# from odoo.addons.website.controllers.main import Website
# from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController
# from odoo.addons.website_sale.controllers.main import TableCompute
# from odoo.addons.website_form.controllers.main import WebsiteForm
# from odoo.osv import expression
# _logger = logging.getLogger(__name__)


# PPG = 20  # Products Per Page
# PPR = 4   # Products Per Row

# class WebsiteSale(ProductConfiguratorController):

# 	def _get_compute_currency(self, pricelist, product=None):
# 		company = product and product._get_current_company(pricelist=pricelist, website=request.website) or pricelist.company_id or request.website.company_id
# 		from_currency = (product or request.env['res.company']._get_main_company()).currency_id
# 		to_currency = pricelist.currency_id
# 		return lambda price: from_currency._convert(price, to_currency, company, fields.Date.today())

# 	def _get_search_order(self, post):
# 		# OrderBy will be parsed in orm and so no direct sql injection
# 		# id is added to be sure that order is a unique sort key
# 		order = post.get('order') or 'website_sequence ASC'
# 		return 'is_published desc, %s, id desc' % order

# 	def _get_search_domain(self, search, category, attrib_values, filter_values, brand_set):
# 		domain = request.website.sale_product_domain()
# 		if search:
# 			for srch in search.split(" "):
# 				domain += [
# 					'|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
# 					('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

# 		if category:
# 			domain += [('public_categ_ids', 'child_of', int(category))]

# 		if attrib_values:
# 			attrib = None
# 			ids = []
# 			for value in attrib_values:
# 				if not attrib:
# 					attrib = value[0]
# 					ids.append(value[1])
# 				elif value[0] == attrib:
# 					ids.append(value[1])
# 				else:
# 					domain += [('attribute_line_ids.value_ids', 'in', ids)]
# 					attrib = value[0]
# 					ids = [value[1]]
# 			if attrib:
# 				domain += [('attribute_line_ids.value_ids', 'in', ids)]


# 		if filter_values:
# 			filter = None
# 			ids = []
# 			for value in filter_values:
# 				if not filter:
# 					filter = value[0]
# 					ids.append(value[1])
# 				elif value[0] == filter:
# 					ids.append(value[1])
# 				else:
# 					domain += [('filter_ids.filter_value_ids', 'in', ids)]
# 					filter = value[0]
# 					ids = [value[1]]
# 			if filter:
# 				domain += [('filter_ids.filter_value_ids', 'in', ids)]

# 		if brand_set:
# 			brand = None
# 			ids = []
# 			for value in brand_set:
# 				ids.append(value)
# 				domain += [('brand_id', 'in', ids)]

# 		return domain

# 	@http.route([
# 		'/shop',
# 		'/shop/page/<int:page>',
# 		'/shop/category/<model("product.public.category"):category>',
# 		'/shop/category/<model("product.public.category"):category>/page/<int:page>'
# 	], type='http', auth="public", website=True)
# 	def shop(self, page=0, category=None, search='', ppg=False, **post):
# 		add_qty = int(post.get('add_qty', 1))
# 		if category:
# 			category = request.env['product.public.category'].search([('id', '=', int(category))], limit=1)
# 			if not category or not category.can_access_from_current_website():
# 				raise NotFound()
# 		if ppg:
# 			try:
# 				ppg = int(ppg)
# 			except ValueError:
# 				ppg = PPG
# 			post["ppg"] = ppg
# 		else:
# 			ppg = PPG

# 		attrib_list = request.httprequest.args.getlist('attrib')
# 		attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
# 		attributes_ids = {v[0] for v in attrib_values}
# 		attrib_set = {v[1] for v in attrib_values}
# 		brand = request.httprequest.args.getlist('brand')
# 		brand_set1 = [[int(x) for x in v] for v in brand if v]
# 		brand_set = [v[0] for v in brand_set1]
# 		filter_list = request.httprequest.args.getlist('filter')
		
# 		filter_values = [[int(x) for x in v.split("-")] for v in filter_list if v]
# 		filter_ids = {v[0] for v in filter_values}
# 		filter_set = {v[1] for v in filter_values}
		
# 		brand_record = request.env['product.brand'].search([('id', 'in', brand_set)])
# 		domain = self._get_search_domain(search, category, attrib_values, filter_values, brand_set)
# 		pricelist_context = dict(request.env.context)
# 		pricelist = False
# 		if not pricelist_context.get('pricelist'):
# 			pricelist = request.website.get_current_pricelist()
# 			pricelist_context['pricelist'] = pricelist.id
# 		else:
# 			pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])
# 		request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

# 		url = "/shop"
# 		if search:
# 			post["search"] = search
# 			AllBrands = request.env['product.brand'].search([('name','ilike',search)])
# 			ids = []
# 			for i in AllBrands:
# 				ids.append(i.id)
# 			domain_new = [('brand_id', 'in', ids)]
			
# 		if category:
# 			category = request.env['product.public.category'].browse(int(category))
# 			url = "/shop/category/%s" % slug(category)
# 		if attrib_list:
# 			post['attrib'] = attrib_list
		
# 		if brand_set:
# 			post['brand'] = brand_set
# 		if filter_list:
# 			post['filter'] = filter_list
		
# 		categs = request.env['product.public.category'].search([('parent_id', '=', False)])
# 		Product = request.env['product.template']
# 		Category = request.env['product.public.category']
		
# 		search_categories = False
# 		if search:
# 			categories = Product.search(domain).mapped('public_categ_ids')
# 			search_categories = Category.search([('id', 'parent_of', categories.ids)] + request.website.website_domain())
# 			categs = search_categories.filtered(lambda c: not c.parent_id)
# 		else:
# 			categs = Category.search([('parent_id', '=', False)] + request.website.website_domain())

# 		parent_category_ids = []
# 		if category:	
# 			parent_category_ids = [category.id]
# 			current_category = category
# 			while current_category.parent_id:
# 				parent_category_ids.append(current_category.parent_id.id)
# 				current_category = current_category.parent_id

# 		product_count = Product.search_count(domain)
# 		pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
# 		products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

# 		ProductAttribute = request.env['product.attribute']
# 		ProductBrand = request.env['product.brand']
# 		ProductFilter = request.env['product.filter']

# 		if not products:
# 			products = Product.search(domain_new, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

		
# 		if products:
# 			# get all products without limit
# 			selected_products = Product.search(domain, limit=False)
# 			attributes = ProductAttribute.search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
# 			brands = ProductBrand.search([])
# 		else:
# 			attributes = ProductAttribute.browse(attributes_ids)
# 			brands = ProductBrand.browse(brand_set)
# 		filters = grouped_tasks = None
# 		if products:
# 			# get all products without limit
# 			selected_products = Product.search(domain, limit=False)
			
# 			filters = ProductFilter.search([('filter_value_ids', '!=', False), ('filter_ids.product_tmpl_id', 'in', selected_products.ids)])
			
# 		else:
# 			filters = ProductFilter.browse(filter_ids)

# 		filter_group = request.env['group.filter'].search([])
		
# 		applied_filter = False
# 		if filter_values:
# 			applied_filter = True

# 		if filter_group:
# 			grouped_tasks = [request.env['product.filter'].concat(*g) for k, g in groupbyelem(filters, itemgetter('group_id'))]
# 		else:
# 			grouped_tasks = [filters]

# 		prods  = Product.sudo().search(domain)
# 		request.website.sudo().get_dynamic_count(prods)
		
# 		keep = QueryURL('/shop', category=category and int(category), search=search,brand=brand_set, attrib=attrib_list, order=post.get('order'))
# 		values = {
# 			'search': search,
# 			'category': category,
# 			'attrib_values': attrib_values,
# 			'attrib_set': attrib_set,
# 			'brand_set': brand_set,
# 			'brand_record': brand_record,
# 			'filter_set': filter_set,
# 			'filter_values': filter_values,
# 			'pager': pager,
# 			'pricelist': pricelist,
# 			'grouped_tasks':grouped_tasks,
# 			'add_qty': add_qty,
# 			'products': products,
# 			'search_count': product_count,  # common for all searchbox
# 			'bins': TableCompute().process(products, ppg),
# 			'rows': PPR,
# 			'categories': categs,
# 			'filters': filters,
# 			'attributes': attributes,
# 			'brands':brands,
# 			'keep': keep,
# 			'parent_category_ids': parent_category_ids,
# 			'search_categories_ids': search_categories and search_categories.ids,
		
# 		}
# 		if category:
# 			values['main_object'] = category
# 		return request.render("website_sale.products", values)