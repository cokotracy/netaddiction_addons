# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    is_b2b = fields.Boolean(
        related='sale_id.is_b2b',
        string="Is a B2B"
    )
