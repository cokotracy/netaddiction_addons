# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    customer = fields.Boolean(
        default=True,
        string="Is a Customer",
    )

    customer_rank = fields.Integer(
        compute='compute_customer_rank',
        store=True,
    )

    supplier = fields.Boolean(
        string="Is a Vendor",
    )

    supplier_rank = fields.Integer(
        compute='compute_supplier_rank',
        store=True,
    )

    @api.depends('customer')
    def compute_customer_rank(self):
        for partner in self:
            # Partners are considered customers when the rank is > 0
            partner.customer_rank = int(partner.customer)

    @api.depends('supplier')
    def compute_supplier_rank(self):
        for partner in self:
            # Partners are considered suppliers when the rank is > 0
            partner.supplier_rank = int(partner.supplier)

    @api.model
    def _name_search(self,
                     name,
                     args=None,
                     operator='ilike',
                     limit=100,
                     name_get_uid=None):
        # Filter out partners basing on the customer/supplier flag,
        # otherwise they would only be ordered basing on their rank.
        args = list(args or [])
        search_mode = self.env.context.get('res_partner_search_mode')
        if search_mode == 'customer':
            args.append(('customer', '=', True))
        if search_mode == 'supplier':
            args.append(('supplier', '=', True))
        return super()._name_search(name, args, operator, limit, name_get_uid)
