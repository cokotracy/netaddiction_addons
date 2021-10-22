# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    is_b2b = fields.Boolean(
        string="Is a B2B",
        compute='_get_partner_data_b2b',
        store=True,
    )

    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _get_partner_data_b2b(self):
        for order in self:
            order.is_b2b = \
                order.partner_id.is_b2b \
                if order.partner_id \
                else False

