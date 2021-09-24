from datetime import date

from odoo.http import request, route, Controller


class CustomHome(Controller):
    @route("/", type="http", auth="public", website=True)
    def controller(self, **post):
        preorder_list = (
            request.env["product.template"]
            .sudo()
            .search([("out_date", ">", date.today().strftime("%Y-%m-%d"))], limit=20)
        )
        return request.render("netaddiction_theme_rewrite.template_home_secondary", {"preorder_list": preorder_list})
