# Copyright 2021 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_id = fields.Many2one(
        'account.payment',
        string='Pagamento',
    )
