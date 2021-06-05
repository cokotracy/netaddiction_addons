# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_method_id = fields.Many2one(
        'account.journal',
        string='Payment method'
    )

    payment_method_name = fields.Char(
        related='payment_method_id.name',
        string='Payment Method Name'
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_payment = fields.Boolean(
        string="Is a Payment"
    )
