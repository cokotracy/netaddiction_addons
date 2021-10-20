from datetime import date

from odoo.http import request, route, Controller


class CustomHome(Controller):
    @route("/", type="http", auth="public", website=True)
    def controller(self, **post):
        if request.website.isB2B:
            return request.redirect('/shop')

        preorder_list = (
            request.env["product.template"]
            .sudo()
            .search([("out_date", ">", date.today())], limit=21, order="create_date desc")
        )
        
        return request.render("netaddiction_website.template_home_primary", {"preorder_list": preorder_list})

class CustomCategoryPage(Controller):
    @route("/lego-shop", type="http", auth="public", website=True)
    def controller(self):
        return request.render("netaddiction_website.template_lego_shop", {})