from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_payment = fields.Boolean(
        string="Is a Payment"
    )
