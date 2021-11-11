from odoo.http import request, Controller
from odoo import http
from datetime import date, datetime
import ast
from operator import itemgetter

MAX_PRICE_RANGE = 950

class CustomPageOffer(Controller):
    @http.route(
        ['/offerte/<model("product.pricelist.dynamic.domain"):pricelist>'], type="http", auth="public", website=True
    )
    def controllerOffer(self, pricelist, **kw):
        current_website = request.website
        current_url = request.httprequest.full_path
        tag_filter = request.params.get("tag-filter")
        max_price = request.params.get("max-price")
        order = request.params.get("order")

        if not "/web/login" in current_url:
            if current_website.isB2B and request.env.user.id == request.env.ref("base.public_user").id:
                return request.redirect("/web/login")
            else:
                if (
                    current_website.isB2B
                    and not request.env.user.is_b2b
                    and not request.env.user.has_group("base.group_user")
                ):
                    request.session.logout()
                    return request.redirect("https://multiplayer.com")

        if not pricelist:
            page = request.website.is_publisher() and "website.page_404" or "http_routing.404"
            return request.render(page, {})

        else:
            if pricelist.pricelist_id.is_b2b and (
                not request.env.user.is_b2b or not request.env.user.has_group("base.group_user")
            ):
                page = request.website.is_publisher() and "website.page_404" or "http_routing.404"
                return request.render(page, {})

            page_size = 24
            start_element = 0
            current_page = 0

            domain = pricelist.complete_products_domain

            if domain:
                if kw.get("page"):
                    current_page = int(kw.get("page")) - 1
                    start_element = page_size * (int(kw.get("page")) - 1)

                domain = ast.literal_eval(domain)

                prod_list = request.env["product.product"].sudo().search(domain).product_tmpl_id

                if tag_filter:
                    tag_list = []
                    tag_filter = tag_filter.split(",")
                    for tag in tag_filter:
                        tag_list.append(int(tag))

                    tag_prod = (
                        request.env["product.template.tag"].sudo().browse(tag_list).product_tmpl_ids
                    )
                    prod_list = prod_list.sudo().filtered_domain([("id", "in", tag_prod.ids)])

                if max_price:
                    if int(max_price) < MAX_PRICE_RANGE:
                        prod_list = prod_list.sudo().filtered_domain(
                            [("product_variant_ids.fix_price", "<=", float(max_price))]
                        )
                    else:
                        prod_list = prod_list.sudo().filtered_domain(
                            [("product_variant_ids.fix_price", ">=", float(max_price))]
                        )

                tags_list = (
                    request.env["product.template.tag"].sudo().search([("product_tmpl_ids", "in", prod_list.ids)])
                )

                if order:
                    order = order.split("-")
                    if len(order) > 1:
                        rev = False
                        if order[1] == "asc":
                            rev = True

                        prod_list = sorted(prod_list, key=itemgetter(order[0]), reverse=rev)

                product_count = len(prod_list)
                end = page_size * (current_page + 1)
                if end > product_count:
                    end = product_count

                product_list_id = prod_list[start_element:end]

                page_number = product_count / page_size

                if page_number > int(page_number):
                    page_number = page_number + 1

                query = ""
                tag = ""
                if "tag-filter" in request.params:
                    tag = request.params["tag-filter"]

                price = ""
                if "max-price" in request.params:
                    price = request.params["max-price"]

                order = ""
                if "order" in request.params:
                    price = request.params["order"]

                query = "tag-filter=" + tag + "&&max-price=" + price + "&&order=" + order

                values = {
                    "query": query,
                    "tags": tags_list,
                    "offer": pricelist,
                    "page_number": int(page_number),
                    "current_page": current_page,
                    "page_size": page_size,
                    "product_list_id": product_list_id,
                }
                return request.render("netaddiction_special_offers.offer_template", values)

    @http.route(['/promozioni/<model("coupon.program"):promotion>'], type="http", auth="public", website=True)
    def controllerPromo(self, promotion, **kw):
        current_website = request.website
        current_url = request.httprequest.full_path
        tag_filter = request.params.get("tag-filter")
        max_price = request.params.get("max-price")
        order = request.params.get("order")

        if not "/web/login" in current_url:
            if current_website.isB2B and request.env.user.id == request.env.ref("base.public_user").id:
                return request.redirect("/web/login")
            else:
                if (
                    current_website.isB2B
                    and not request.env.user.is_b2b
                    and not request.env.user.has_group("base.group_user")
                ):
                    request.session.logout()
                    return request.redirect("https://multiplayer.com")

        if not promotion:
            page = request.website.is_publisher() and "website.page_404" or "http_routing.404"
            return request.render(page, {})

        if promotion.active and promotion.rule_date_from <= datetime.now() and promotion.rule_date_to >= datetime.now():

            page_size = 24
            start_element = 0
            current_page = 0

            domain = promotion.rule_products_domain

            if domain:
                if kw.get("page"):
                    current_page = int(kw.get("page")) - 1
                    start_element = page_size * (int(kw.get("page")) - 1)

                domain = ast.literal_eval(domain)

                prod_list = None
                if promotion.discount_specific_product_ids:
                    prod_list = promotion.discount_specific_product_ids.product_tmpl_id
                else:
                    prod_list = request.env["product.product"].sudo().search(domain).product_tmpl_id

                if tag_filter:
                    tag_list = []
                    tag_filter = tag_filter.split(",")
                    for tag in tag_filter:
                        tag_list.append(int(tag))

                    tag_prod = (
                        request.env["product.template.tag"].sudo().browse(tag_list).product_tmpl_ids
                    )
                    prod_list = prod_list.sudo().filtered_domain([("id", "in", tag_prod.ids)])

                if max_price:
                    if int(max_price) < MAX_PRICE_RANGE:
                        prod_list = prod_list.sudo().filtered_domain(
                            [("product_variant_ids.fix_price", "<=", float(max_price))]
                        )
                    else:
                        prod_list = prod_list.sudo().filtered_domain(
                            [("product_variant_ids.fix_price", ">=", float(max_price))]
                        )

                tags_list = (
                    request.env["product.template.tag"].sudo().search([("product_tmpl_ids", "in", prod_list.ids)])
                )

                if order:
                    order = order.split("-")
                    if len(order) > 1:
                        rev = False
                        if order[1] == "asc":
                            rev = True
                            
                        prod_list = sorted(prod_list, key=itemgetter(order[0]), reverse=rev)

                product_count = len(prod_list)
                end = page_size * (current_page + 1)
                if end > product_count:
                    end = product_count

                product_list_id = prod_list[start_element:end]

                page_number = product_count / page_size

                if page_number > int(page_number):
                    page_number = page_number + 1

                query = ""
                tag = ""
                if "tag-filter" in request.params:
                    tag = request.params["tag-filter"]

                price = ""
                if "max-price" in request.params:
                    price = request.params["max-price"]

                order = ""
                if "order" in request.params:
                    price = request.params["order"]

                query = "tag-filter=" + tag + "&&max-price=" + price + "&&order=" + order

                values = {
                    "query": query,
                    "tags": tags_list,
                    "promo": promotion,
                    "page_number": int(page_number),
                    "current_page": current_page,
                    "page_size": page_size,
                    "product_list_id": product_list_id,
                }
                return request.render("netaddiction_special_offers.promotion_template", values)
        else:
            page = request.website.is_publisher() and "website.page_404" or "http_routing.404"
            return request.render(page, {})
