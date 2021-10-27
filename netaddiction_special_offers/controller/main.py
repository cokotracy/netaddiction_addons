from odoo.http import request, Controller
from odoo import  http
from datetime import date
import ast


class CustomPageOffer(Controller):
    @http.route(['/offerte/<model("product.pricelist.dynamic.domain"):pricelist>'], type="http", auth="public", website=True)
    def controllerOffer(self, pricelist, **kw):
        current_website = request.website
        current_url = request.httprequest.full_path

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

            page_size = 21
            start_element = 0
            current_page = 0

            domain = pricelist.complete_products_domain

            if domain:
                if kw.get("page"):
                    current_page = int(kw.get("page")) - 1
                    start_element = page_size * (int(kw.get("page")) - 1)

                domain = ast.literal_eval(domain)

                product_count = request.env["product.product"].sudo().search_count(domain)
                product_list_id = (
                    request.env["product.product"]
                    .sudo()
                    .search(domain, limit=page_size, offset=start_element)
                    .product_tmpl_id
                )

                page_number = product_count / page_size

                if page_number > int(page_number):
                    page_number = page_number + 1

                values = {
                    "offer_id": pricelist.id,
                    "offer_name": pricelist.name,
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

        else:
            page_size = 21
            start_element = 0
            current_page = 0

            domain = promotion.rule_products_domain

            if domain:
                if kw.get("page"):
                    current_page = int(kw.get("page")) - 1
                    start_element = page_size * (int(kw.get("page")) - 1)

                domain = ast.literal_eval(domain)

                product_count = request.env["product.product"].sudo().search_count(domain)
                product_list_id = (
                    request.env["product.product"]
                    .sudo()
                    .search(domain, limit=page_size, offset=start_element)
                    .product_tmpl_id
                )

                page_number = product_count / page_size

                if page_number > int(page_number):
                    page_number = page_number + 1

                values = {
                    "promo_id": promotion.id,
                    "promo_name": promotion.name,
                    "page_number": int(page_number),
                    "current_page": current_page,
                    "page_size": page_size,
                    "product_list_id": product_list_id,
                }
                return request.render("netaddiction_special_offers.promotion_template", values)