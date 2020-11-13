# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    out_date = fields.Date()


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _order = 'name, id'

    default_code = fields.Char(
        string='Internal Reference',
        compute='compute_default_code',
        search='search_default_code',
        readonly=True,
        index=True,
    )

    final_price = fields.Float(
        string="Pricelist Price",
        digits='Product Price'
    )

    qty_available_now = fields.Integer(
        compute="_get_qty_available_now",
        # search="_search_available_now",
        string="Quantità Disponibile",
        help="Quantità Disponibile Adesso (qty in possesso - qty in uscita)")

    def compute_default_code(self):
        for product in self:
            product.default_code = str(product.id)

    def search_default_code(self, operator, value):
        return [('id', operator, value)]

    def _get_qty_available_now(self):
        for product in self:
            product.qty_available_now = \
                product.qty_available - product.outgoing_qty


class SupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'

    avail_qty = fields.Float(
        string='Available Qty'
    )
