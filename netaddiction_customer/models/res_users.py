# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        Partner = self.env['res.partner']
        for item in vals_list:
            partner = Partner.search([('email', '=', item['email'])])
            if partner:
                item['partner_id'] = partner.id
        users = super().create(vals_list)
        return users
