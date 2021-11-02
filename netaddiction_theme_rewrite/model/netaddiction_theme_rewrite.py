# Copyright 2021 Netaddiction

# Documentation links
# https://www.odoo.com/documentation/12.0/reference/http.html

from werkzeug.exceptions import Forbidden, NotFound
from datetime import date, timedelta, datetime
from odoo.http import request, route, Controller
from odoo import models, fields, tools, http, _
from odoo.exceptions import AccessError, ValidationError
from odoo.addons.odoo_website_wallet.controllers.main import WebsiteWallet as Wallet
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.website_sale_stock.controllers.main import WebsiteSaleStock
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.payment.controllers.portal import WebsitePayment

import ast
from odoo.osv import expression


class WebsiteCustom(Website):
    @route(["/shop/cart/check_limit_order"], type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def cart_update_json(self):
        if request.env.user.id == request.env.ref("base.public_user").id:
            return request.redirect("/web/login")

        order = request.website.sale_get_order(force_create=1)
        for order_line in order.order_line:
            prod = order_line.product_id

            if prod.type != "service":
                if prod.qty_single_order > 0:
                    if order_line.product_qty > prod.qty_single_order:
                        return {
                            "image": prod.image_512,
                            "order_limit": prod.qty_single_order,
                            "product_name": prod.name,
                            "qty_available_now": prod.qty_available_now,
                            "qty_sum_suppliers": prod.sudo().qty_sum_suppliers,
                            "out_date": prod.out_date,
                            "sale_ok": prod.sale_ok,
                        }

                if prod.qty_limit > 0:
                    # FIXME
                    orders = request.env["sale.order.line"].sudo().search([("product_id", "=", prod.id)])
                    sold = 0
                    for order in orders:
                        sold = sold + order.product_qty

                    if (sold + order_line.product_qty) >= prod.qty_limit:
                        return {
                            "image": prod.image_512,
                            "order_limit_total": prod.qty_limit,
                            "product_name": prod.name,
                            "qty_available_now": prod.qty_available_now,
                            "qty_sum_suppliers": prod.sudo().qty_sum_suppliers,
                            "out_date": prod.out_date,
                            "sale_ok": prod.sale_ok,
                        }

                if prod.sudo().qty_sum_suppliers <= 0 and prod.qty_available_now <= 0:
                    if (
                        not prod.out_date
                        or prod.out_date < date.today()
                        or prod.sudo().inventory_availability != "never"
                    ):
                        return {"image": prod.image_512, "out_of_stock": True, "product_name": prod.name}

                if prod.sale_ok == False:
                    return {"image": prod.image_512, "out_of_stock": True, "product_name": prod.name}

    @route(["/get_product_from_id"], type="json", auth="public", website=True, csrf=False)
    def get_product_from_id(self, product_id=None):
        prod = request.env["product.product"].search([("id", "=", product_id)])
        current = date.today()
        current_reduced = datetime.now() - timedelta(days=20)
        prod_out_date = ""
        out_over_current = False
        its_new = False

        if prod.out_date:
            prod_out_date = prod.out_date
            if prod_out_date > current:
                out_over_current = True

        return {
            "current": current,
            "current_reduced": (current_reduced <= prod.create_date),
            "prod_out_date": prod_out_date,
            "qty_sum_suppliers": prod.sudo().qty_sum_suppliers,
            "sale_ok": prod.sale_ok,
            "qty_available_now": prod.qty_available_now,
            "out_date": prod.out_date,
            "create_date": prod.create_date,
            "inventory_availability": prod.sudo().inventory_availability,
            "user_email": "" if not request.env.user.email else request.env.user.email,
            "out_over_current": out_over_current,
            "its_new": its_new,
        }


class WebsiteSaleStockCustom(WebsiteSaleStock, WebsiteSale):
    @route()
    def payment_transaction(self, *args, **kwargs):
        """Payment transaction override to double check cart quantities before
        placing the order
        """
        order = request.website.sale_get_order()
        values = []
        for line in order.order_line:
            if line.product_id.type == "product" and line.product_id.inventory_availability in ["always", "threshold"]:
                cart_qty = sum(
                    order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped("product_uom_qty")
                )
                avl_qty = line.product_id.with_context(warehouse=order.warehouse_id.id).virtual_available
                if cart_qty > avl_qty and line.product_id.sudo().qty_sum_suppliers <= 0:

                    values.append(
                        _(
                            "You ask for %(quantity)s products but only %(available_qty)s is available",
                            quantity=cart_qty,
                            available_qty=avl_qty if avl_qty > 0 else 0,
                        )
                    )
        if values:
            raise ValidationError(". ".join(values) + ".")

        return WebsiteSale.payment_transaction(self, *args, **kwargs)


class WebsiteSaleCustom(WebsiteSale):
    #     @route(['/shop/payment'], type='http', auth="public", website=True)
    #     def payment(self, **post):
    #         prod_id = request.params.get("buynow")

    #         if prod_id:
    #             if request.env.user.id == request.env.ref('base.public_user').id:
    #                 return request.redirect('/web/login')

    #             order = request.env['sale.order'].sudo().create({
    #                 'partner_id': request.env.user.id,
    #                 'website_id': request.website.id,
    #             })
    #             request.env['sale.order.line'].sudo().create({
    #                 "order_id":order.id,
    #                 "product_id":int(prod_id),
    #                 "product_uom_qty":1,
    #             })

    #             render_values = self._get_shop_payment_values(order, **post)
    #             render_values['only_services'] = order and order.only_services or False

    #             if render_values['errors']:
    #                 render_values.pop('acquirers', '')
    #                 render_values.pop('tokens', '')

    #             return request.render("website_sale.payment", render_values)

    #         return super(WebsiteSaleCustom, self).payment(**post)
    @route(
        [
            """/shop""",
            """/shop/page/<int:page>""",
            """/shop/category/<model("product.public.category"):category>""",
            """/shop/category/<model("product.public.category"):category>/page/<int:page>""",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=WebsiteSale.sitemap_shop,
    )
    def shop(self, page=0, category=None, search="", ppg=False, **post):
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

        add_qty = int(post.get("add_qty", 1))

        status_filter = request.params.get("status-filter")
        search = request.params.get("search")
        tag_filter = request.params.get("tag-filter")

        Category = request.env["product.public.category"]

        preorder_list = newest_list = bestseller_list = []

        if category:
            category = Category.search([("id", "=", int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if category:
            preorder_list = (
                request.env["product.template"]
                .sudo()
                .search(
                    [
                        ("out_date", ">", date.today().strftime("%Y-%m-%d")),
                        ("type", "!=", "service"),
                        ("public_categ_ids", "in", category.id),
                    ],
                    limit=20,
                )
            )

            newest_list = (
                request.env["product.template"]
                .sudo()
                .search(
                    [
                        ("create_date", ">=", (date.today() - timedelta(days=20)).strftime("%Y-%m-%d")),
                        ("create_date", "<=", date.today().strftime("%Y-%m-%d")),
                        ("type", "!=", "service"),
                        ("public_categ_ids", "in", category.id),
                        "|",
                        ("out_date", "<=", date.today().strftime("%Y-%m-%d")),
                        ("out_date", "=", False),
                    ],
                    limit=20,
                )
            )

            bestseller_list_temp = (
                request.env["sale.order.line"]
                .sudo()
                .read_group(
                    domain=[
                        ("create_date", ">=", (date.today() - timedelta(days=20)).strftime("%Y-%m-%d")),
                        ("create_date", "<=", date.today().strftime("%Y-%m-%d")),
                        ("qty_invoiced", ">", 0),
                        ("product_id.product_tmpl_id.public_categ_ids", "in", category.id),
                    ],
                    fields=["product_id"],
                    groupby=["product_id"],
                    limit=20,
                    orderby="qty_invoiced desc",
                )
            )

            for bs in bestseller_list_temp:
                try:
                    product = request.env["product.product"].sudo().search([("id", "=", bs["product_id"][0])])
                    if product:
                        bestseller_list.append(product.product_tmpl_id)
                except Exception:
                    pass

        if ppg:
            try:
                ppg = int(ppg)
                post["ppg"] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env["website"].get_current_website().shop_ppg or 20

        ppr = request.env["website"].get_current_website().shop_ppr or 4

        attrib_list = request.httprequest.args.getlist("attrib")
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values)
        domain = expression.AND([[("type", "!=", "service")], domain])

        keep = QueryURL(
            "/shop", category=category and int(category), search=search, attrib=attrib_list, order=post.get("order")
        )

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post["attrib"] = attrib_list

        Product = request.env["product.template"].with_context(bin_size=True)

        if tag_filter:
            tag_filter = tag_filter.split(",")

        if request.website.isB2B and not status_filter:
            domain = expression.AND([[("product_variant_ids.qty_available_now", ">", 0)], domain])
        elif not status_filter:
            new_dom = [
                "|",
                ("product_variant_ids.out_date", ">", date.today()),
                ("product_variant_ids.qty_available_now", ">", 0),
            ]
            domain = expression.AND([new_dom, domain])

        if status_filter:
            status_filter = status_filter.split(",")
            domain = self._filters_pre_products(filters=status_filter, domain=domain)
        search_product = Product.search(domain, order=self._custom_get_search_order(post))
        if status_filter:
            search_product = self._filters_post_products(filters=status_filter, products=search_product)

        website_domain = request.website.website_domain()
        categs_domain = [("parent_id", "=", False)] + website_domain
        if search:
            search_categories = Category.search(
                [("product_tmpl_ids", "in", search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(("id", "in", search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager["offset"]
        products = search_product[offset : offset + ppg]

        ProductAttribute = request.env["product.attribute"]
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([("product_tmpl_ids", "in", search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = request.session.get("website_sale_shop_layout_mode")
        if not layout_mode:
            if request.website.viewref("website_sale.products_list_view").active:
                layout_mode = "list"
            else:
                layout_mode = "grid"

        tableComp = TableCompute()
        bins = tableComp.process(products, ppg, ppr)

        values = {
            "preorder_list": preorder_list,
            "newest_list": newest_list,
            "bestseller_list": bestseller_list,
            "search": search,
            "category": category,
            "attrib_values": attrib_values,
            "attrib_set": attrib_set,
            "pager": pager,
            "pricelist": pricelist,
            "add_qty": add_qty,
            "products": products,
            "search_count": product_count,  # common for all searchbox
            "bins": bins,
            "ppg": ppg,
            "ppr": ppr,
            "categories": categs,
            "attributes": attributes,
            "keep": keep,
            "search_categories_ids": search_categories.ids,
            "layout_mode": layout_mode,
        }
        if category:
            values["main_object"] = category
        return request.render("website_sale.products", values)

    def _custom_get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        order = post.get("order") or "create_date desc"
        return "is_published desc, %s" % order

    def _filters_pre_products(self, filters, domain):
        if len(filters) == 1:
            for filter in filters:
                if filter == "stock":
                    domain = expression.AND([[("product_variant_ids.qty_available_now", ">", 0)], domain])

                if filter == "preorder":
                    domain = expression.AND([[("product_variant_ids.out_date", ">", date.today())], domain])

                if filter == "new":
                    domain = expression.AND([[("create_date", ">", (date.today() - timedelta(days=20)))], domain])
        else:
            if len(filters) > 1:
                new_domain = ["|"]
                for filter in filters:
                    if filter == "stock":
                        new_domain.append(("product_variant_ids.qty_available_now", ">", 0))

                    if filter == "preorder":
                        new_domain.append(("product_variant_ids.out_date", ">", date.today()))

                    if filter == "new":
                        new_domain.append(("create_date", ">", (date.today() - timedelta(days=20))))

                domain = expression.AND([new_domain, domain])

        return domain

    def _filters_post_products(self, filters, products):
        for filter in filters:
            if filter == "order":
                products = products.sudo().filtered_domain([("product_variant_ids.qty_sum_suppliers", ">", 0)])
            if filter == "unavailable":
                products = products.sudo().filtered_domain(
                    [
                        ("product_variant_ids.qty_sum_suppliers", "<=", 0),
                        ("product_variant_ids.qty_available_now", "<=", 0),
                        "|",
                        ("product_variant_ids.out_date", "=", ""),
                        ("product_variant_ids.out_date", "<", date.today()),
                    ],
                )
        return products


# AGGIUNGE LA PAGINA PRIVACY
class CustomPrivacy(Controller):
    @route("/privacy/", type="http", auth="public", website=True)
    def controller(self, **post):
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

        return request.render("netaddiction_theme_rewrite.template_privacy_policy", {})


class CustomCustomerPortal(Controller):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "street2", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name"]

    _items_per_page = 20

    def details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = "missing"

        # email validation
        if data.get("email") and not tools.single_email_re.match(data.get("email")):
            error["email"] = "error"
            error_message.append(_("Email non valida!"))

        # error message for empty required fields
        if [err for err in error.values() if err == "missing"]:
            error_message.append(_("Non hai inserito dei campi obbligatori!"))

        unknown = [k for k in data if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error["common"] = "Unknown field"
            error_message.append("Campo sconosciuto '%s'" % ",".join(unknown))

        return error, error_message

    def _prepare_portal_layout_values(self):
        """Values for /my/* templates rendering.

        Does not include the record counts.
        """
        # get customer sales rep
        sales_user = False
        partner = request.env.user.partner_id
        if partner.user_id and not partner.user_id._is_public():
            sales_user = partner.user_id

        return {
            "sales_user": sales_user,
            "page_name": "home",
        }

    @route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update(
            {
                "error": {},
                "error_message": [],
            }
        )

        if post and request.httprequest.method == "POST":
            error, error_message = self.details_form_validate(post)
            values.update({"error": error, "error_message": error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(["country_id", "state_id"]) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except Exception:
                        values[field] = False
                values.update({"zip": values.pop("zipcode", "")})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect("/my/home")

        countries = request.env["res.country"].sudo().search([])
        states = request.env["res.country.state"].sudo().search([])

        values.update(
            {
                "partner": partner,
                "countries": countries,
                "states": states,
                "has_check_vat": hasattr(request.env["res.partner"], "check_vat"),
                "redirect": redirect,
                "page_name": "my_details",
                "context": {"no_breadcrumbs": True},
            }
        )

        response = request.render("netaddiction_theme_rewrite.custom_portal_my_details", values)
        response.headers["X-Frame-Options"] = "DENY"
        return response


# AGGIUNGE LA PAGINA COSTI DI SPEDIZIONE
class CustomShipping(Controller):
    @route("/costi-metodi-spedizione/", type="http", auth="public", website=True)
    def controller(self, **post):
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

        return request.render("netaddiction_theme_rewrite.template_shipping_terms", {})


class CustomListPage(Controller):
    @route(["/tag/<string:tag_name>"], type="http", auth="public", website=True)
    def controllerTag(self, tag_name, **kw):
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

        status_filter = request.params.get("status-filter")
        tag = request.env["product.template.tag"].sudo().search([("name", "=", tag_name)], limit=1)
        domain = [("tag_ids", "=", tag.id)]

        if not tag.id:
            page = request.website.is_publisher() and "website.page_404" or "http_routing.404"
            return request.render(page, {})

        else:
            if not status_filter:
                new_dom = [
                    "|",
                    ("product_variant_ids.out_date", ">", date.today()),
                    ("product_variant_ids.qty_available_now", ">", 0),
                ]
                domain = expression.AND([new_dom, domain])
            else:
                status_filter = status_filter.split(",")
                domain = self._filters_pre_products(filters=status_filter, domain=domain)

            page_size = 24
            start_element = 0
            current_page = 0

            if kw.get("page"):
                current_page = int(kw.get("page")) - 1
                start_element = page_size * (int(kw.get("page")) - 1)

            product_count = request.env["product.template"].sudo().search_count(domain)

            product_list_id = (
                request.env["product.template"].sudo().search(domain, limit=page_size, offset=start_element)
            )

            page_number = product_count / page_size

            if page_number > int(page_number):
                page_number = page_number + 1

            values = {
                "tag_name": tag_name,
                "page_number": int(page_number),
                "current_page": current_page,
                "page_size": page_size,
                "product_list_id": product_list_id,
            }
            return request.render("netaddiction_theme_rewrite.template_tag", values)

    def _filters_pre_products(self, filters, domain):
        if len(filters) == 1:
            for filter in filters:
                if filter == "stock":
                    domain = expression.AND([[("product_variant_ids.qty_available_now", ">", 0)], domain])

                if filter == "preorder":
                    domain = expression.AND([[("product_variant_ids.out_date", ">", date.today())], domain])

                if filter == "new":
                    domain = expression.AND([[("create_date", ">", (date.today() - timedelta(days=20)))], domain])
        else:
            if len(filters) > 1:
                new_domain = ["|"]
                for filter in filters:
                    if filter == "stock":
                        new_domain.append(("product_variant_ids.qty_available_now", ">", 0))

                    if filter == "preorder":
                        new_domain.append(("product_variant_ids.out_date", ">", date.today()))

                    if filter == "new":
                        new_domain.append(("create_date", ">", (date.today() - timedelta(days=20))))

                domain = expression.AND([new_domain, domain])

        return domain


# ESTENDE LA WALLET BALANCE PAGE
class WalletPageOverride(Wallet):
    @route(["/wallet"], type="http", auth="public", website=True)
    def wallet_balance(self, **post):
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

        sup = super(WalletPageOverride, self).wallet_balance()
        return request.render("netaddiction_theme_rewrite.wallet_balance", sup.qcontext)

    @route(["/add/wallet/balance"], type="http", auth="public", website=True)
    def add_wallet_balance(self, **post):
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

        sup = super(WalletPageOverride, self).add_wallet_balance()
        return request.render("netaddiction_theme_rewrite.add_wallet_balance", sup.qcontext)


# CUSTOM ADDRESS TEMPLATE
class WebsiteSaleCustomAddress(Controller):
    @route(["/shop/address"], type="http", methods=["GET", "POST"], auth="public", website=True, sitemap=False)
    def address(self, **kw):
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

            if request.env.user.id == request.env.ref("base.public_user").id:
                return request.redirect("/web/login")

        Partner = request.env["res.partner"].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get("partner_id", -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ("new", "billing")
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ("edit", "billing")
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ("new", "shipping")
                        partner_id = -1
                    elif partner_id in shippings.mapped("id"):
                        mode = ("edit", "shipping")
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ("new", "shipping")
            else:  # no mode - refresh without post?
                return request.redirect("/shop/checkout")

        # IF POSTED
        if "submitted" in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors["error_message"] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == "billing":
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get("use_same"):
                        kw["callback"] = kw.get("callback") or (
                            not order.only_services and (mode[0] == "edit" and "/shop/checkout" or "/shop/address")
                        )
                elif mode[1] == "shipping":
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get("callback") or "/shop/confirm_order")

        render_values = {
            "website_sale_order": order,
            "partner_id": partner_id,
            "mode": mode,
            "checkout": values,
            "can_edit_vat": can_edit_vat,
            "error": errors,
            "callback": kw.get("callback"),
            "only_services": order and order.only_services,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("netaddiction_theme_rewrite.custom_address_checkout", render_values)

    @route(["/my/home/address-edit"], type="http", methods=["GET", "POST"], auth="public", website=True, sitemap=False)
    def address_edit(self, **kw):
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

        Partner = request.env["res.partner"].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get("partner_id", -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ("new", "billing")
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ("edit", "billing")
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ("new", "shipping")
                        partner_id = -1
                    elif partner_id in shippings.mapped("id"):
                        mode = ("edit", "shipping")
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ("new", "shipping")
            else:  # no mode - refresh without post?
                return request.redirect("/shop/checkout")

        # IF POSTED
        if "submitted" in kw:
            partner_fields = request.env["res.partner"]._fields
            pre_values = {
                k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == "many2one" else v
                for k, v in kw.items()
            }
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors["error_message"] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == "billing":
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get("use_same"):
                        kw["callback"] = kw.get("callback") or (
                            not order.only_services and (mode[0] == "edit" and "/shop/checkout" or "/shop/address")
                        )
                elif mode[1] == "shipping":
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect("/my/home")

        render_values = {
            "website_sale_order": order,
            "partner_id": partner_id,
            "mode": mode,
            "checkout": values,
            "can_edit_vat": can_edit_vat,
            "error": errors,
            "callback": kw.get("callback"),
            "only_services": order and order.only_services,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("netaddiction_theme_rewrite.my_address_edit", render_values)

    def checkout_form_validate(self, mode, all_form_values, data):
        # mode: tuple ('new|edit', 'billing|shipping')
        # all_form_values: all values before preprocess
        # data: values after preprocess
        error = dict()
        error_message = []

        # Required fields from form
        required_fields = [f for f in (all_form_values.get("field_required") or "").split(",") if f]

        # Required fields from mandatory field function
        country_id = int(data.get("country_id", False))
        required_fields += (
            mode[1] == "shipping"
            and self._get_mandatory_fields_shipping(country_id)
            or self._get_mandatory_fields_billing(country_id)
        )

        # error message for empty required fields
        for field_name in required_fields:
            if not data.get(field_name):
                error[field_name] = "missing"

        # email validation
        if data.get("email") and not tools.single_email_re.match(data.get("email")):
            error["email"] = "error"
            error_message.append("Email non valida!")

        # vat validation
        Partner = request.env["res.partner"]
        if data.get("vat") and hasattr(Partner, "check_vat"):
            if country_id:
                data["vat"] = Partner.fix_eu_vat_number(country_id, data.get("vat"))
            partner_dummy = Partner.new(self._get_vat_validation_fields(data))
            try:
                partner_dummy.check_vat()
            except ValidationError as exception:
                error["vat"] = "error"
                error_message.append(exception.args[0])

        if [err for err in error.values() if err == "missing"]:
            error_message.append("Non hai inserito dei campi obbligatori!")

        return error, error_message

    def _get_mandatory_fields_billing(self, country_id=False):
        req = self._get_mandatory_billing_fields()
        if country_id:
            country = request.env["res.country"].browse(country_id)
            if country.state_required:
                req += ["state_id"]
            if country.zip_required:
                req += ["zip"]
        return req

    def _get_mandatory_fields_shipping(self, country_id=False):
        req = self._get_mandatory_shipping_fields()
        if country_id:
            country = request.env["res.country"].browse(country_id)
            if country.state_required:
                req += ["state_id"]
            if country.zip_required:
                req += ["zip"]
        return req

    def _get_mandatory_billing_fields(self):
        # deprecated for _get_mandatory_fields_billing which handle zip/state required
        return ["name", "email", "street", "city", "country_id"]

    def _get_mandatory_shipping_fields(self):
        # deprecated for _get_mandatory_fields_shipping which handle zip/state required
        return ["name", "street", "city", "country_id"]

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env["res.partner"]
        if mode[0] == "new":
            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == "edit":
            partner_id = int(all_values.get("partner_id", 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped("id") and partner_id != order.partner_id.id:
                    return Forbidden()
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    def checkout_redirection(self, order):
        # must have a draft sales order with lines at this point, otherwise reset
        if not order or order.state != "draft":
            request.session["sale_order_id"] = None
            request.session["sale_transaction_id"] = None
            return request.redirect("/shop")

        if order and not order.order_line:
            return request.redirect("/shop/cart")

        # if transaction pending / done: redirect to confirmation
        tx = request.env.context.get("website_sale_transaction")
        if tx and tx.state != "draft":
            return request.redirect("/shop/payment/confirmation/%s" % order.id)

    def values_preprocess(self, order, mode, values):
        # Convert the values for many2one fields to integer since they are used as IDs
        partner_fields = request.env["res.partner"]._fields
        return {
            k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == "many2one" else v
            for k, v in values.items()
        }

    def values_postprocess(self, order, mode, values, errors, error_msg, partner_id=None):
        new_values = {}
        authorized_fields = request.env["ir.model"]._get("res.partner")._get_form_writable_fields()
        for k, v in values.items():
            # don't drop empty value, it could be a field to reset
            if k in authorized_fields and v is not None:
                new_values[k] = v

        new_values["team_id"] = request.website.salesteam_id and request.website.salesteam_id.id
        new_values["user_id"] = request.website.salesperson_id and request.website.salesperson_id.id

        if request.website.specific_user_account:
            new_values["website_id"] = request.website.id

        if mode[0] == "new":
            new_values["company_id"] = request.website.company_id.id

        lang = request.lang.code if request.lang.code in request.website.mapped("language_ids.code") else None
        if lang:
            new_values["lang"] = lang
        if mode == ("edit", "billing") and order.partner_id.type == "contact":
            new_values["type"] = "other"
        if mode[1] == "shipping":
            if order:
                new_values["parent_id"] = order.partner_id.commercial_partner_id.id
            else:
                partner_id = partner_id
            new_values["type"] = "delivery"

        return new_values, errors, error_msg

    def _get_country_related_render_values(self, kw, render_values):
        """
        This method provides fields related to the country to render the website sale form
        """
        values = render_values["checkout"]
        mode = render_values["mode"]
        order = render_values["website_sale_order"]

        def_country_id = order.partner_id.country_id
        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            country_code = request.session["geoip"].get("country_code")
            if country_code:
                def_country_id = request.env["res.country"].search([("code", "=", country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id

        country = (
            "country_id" in values
            and values["country_id"] != ""
            and request.env["res.country"].browse(int(values["country_id"]))
        )
        country = country and country.exists() or def_country_id

        res = {
            "country": country,
            "country_states": country.get_website_sale_states(mode=mode[1]),
            "countries": country.get_website_sale_countries(mode=mode[1]),
        }
        return res


class CustomCustomerPortal(CustomerPortal):
    @route(["/my/orders", "/my/orders/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        response = super(CustomCustomerPortal, self).portal_my_orders(page, date_begin, date_end, sortby)
        response = http.Response(
            template="netaddiction_theme_rewrite.custom_portal_my_orders", qcontext=response.qcontext
        )
        return response.render()

    @route(["/my/orders/<int:order_id>"], type="http", auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            self._check_user_permission_order(order_id)
        except (AccessError):
            return request.redirect("/my")
        response = super(CustomCustomerPortal, self).portal_order_page(order_id=order_id)
        return response.render()

    def _check_user_permission_order(self, order_id):
        if request.env.user.has_group("base.group_user"):
            return
        if not request.session.uid:
            raise AccessError("Non hai i permessi per visualizzare questa pagina")
        order = request.env["sale.order"].browse([order_id])
        if not order.with_user(request.session.uid).exists():
            raise AccessError("Non hai i permessi per visualizzare questa pagina")


class CustomWebsitePayment(WebsitePayment):
    @route(["/my/payment_method"], type="http", auth="user", website=True)
    def payment_method(self, **kwargs):
        response = super(CustomWebsitePayment, self).payment_method(**kwargs)
        try:
            acquirer = request.env["payment.acquirer"].search(
                [("provider", "=", "netaddiction_stripe"), ("state", "=", "enabled")]
            )[0]
        except IndexError:
            pass
        else:
            response.qcontext["acquirer_id"] = acquirer.id
            response.qcontext["stripe_key"] = acquirer.netaddiction_stripe_pk
        response = http.Response(
            template="netaddiction_theme_rewrite.custom_portal_my_payment_method", qcontext=response.qcontext
        )
        return response.render()
