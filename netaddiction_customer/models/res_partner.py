# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    street2 = fields.Char(
        string='Civico'
    )

    def _get_name(self):
        name = super()._get_name()
        # Add always partner id in partner name
        name = f'[{self.id}] {name}'
        return name
