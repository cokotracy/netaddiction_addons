from odoo import _, api, fields, models


class ProductsTemplate(models.Model):
    _inherit = 'product.template'

    product_wh_location_line_ids = fields.Boolean(
        string="Inverse"
    )
