# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
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

    def _create_payment_transaction(self, vals):
        transaction = super()._create_payment_transaction(vals)
        if transaction:
            journal = transaction.acquirer_id.journal_id
            self.write(
                {'payment_method_id': journal.id if journal else False})
        return transaction


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_payment = fields.Boolean(
        string="Is a Payment"
    )
