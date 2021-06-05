# Copyright 2020 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    digital_bonus_code_ids = fields.One2many(
        'sale.coupon.program.digital.bonus.code',
        'sale_order_id',
        string='Digital Bonus Codes Used'
    )
