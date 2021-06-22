# Copyright 2021 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_customer = fields.Boolean(
        compute="_compute_is_customer",
        inverse="_inverse_is_customer",
        store=True,
        readonly=False,
        string="Is a Customer",
    )
    is_supplier = fields.Boolean(
        compute="_compute_is_supplier",
        inverse="_inverse_is_supplier",
        store=True,
        readonly=False,
        string="Is a Supplier",
    )

    # On the original Odoo 9 instance, the fields 'customer' and 'supplier'
    # were available, and they are widely used in netaddiction addons. It is
    # impossibile to check each and every line of code where 'customer' and
    # 'supplier' fields are used, and this OCA module has unfortunately
    # changed the fields names to 'is_customer' and 'is_supplier'. The idea
    # of adding 'customer' and 'supplier' back as related is just a
    # quick-and-dirty workaround to prevent errors. These two fields are
    # deprecated and should never be actually used. On the other hand, please
    # remove all references to 'customer' and 'supplier' if you find any

    customer = fields.Boolean(
        related='is_customer',
        string="Is a customer (Deprecated)",
    )

    supplier = fields.Boolean(
        related='is_supplier',
        string="Is a supplier (Deprecated)",
    )

    @api.depends("customer_rank")
    def _compute_is_customer(self):
        for partner in self:
            partner.is_customer = bool(partner.customer_rank)

    @api.depends("supplier_rank")
    def _compute_is_supplier(self):
        for partner in self:
            partner.is_supplier = bool(partner.supplier_rank)

    def _inverse_is_customer(self):
        for partner in self:
            partners = partner | partner.commercial_partner_id
            if partner.is_customer:
                partners._increase_rank("customer_rank")
            else:
                partners.customer_rank = 0

    def _inverse_is_supplier(self):
        for partner in self:
            partners = partner | partner.commercial_partner_id
            if partner.is_supplier:
                partners._increase_rank("supplier_rank")
            else:
                partners.supplier_rank = 0
