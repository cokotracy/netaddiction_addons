# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    is_b2b = fields.Boolean(
        string="Is a B2B"
    )
