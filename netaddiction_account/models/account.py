# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    create_credit_note = fields.Boolean(
        'Crea una nota di credito'
    )

    is_customer_invoice = fields.Boolean(
        string="Invoice"
    )

    customer_number_identifier = fields.Char(
        'Customer Number identifier',
        compute='_get_customer_number_identifier'
    )

    @api.model
    def create(self, values):
        create_credit_note = values.get('create_credit_note', False)
        if create_credit_note:
            values['type'] = 'in_refund'
        return super().create(values)

    @api.multi
    def write(self, values):
        is_customer_invoice = values.get('is_customer_invoice', False)
        if not is_customer_invoice:
            return super().write(values)
        for invoice in self:
            if not (invoice.partner_id.fiscalcode or invoice.partner_id.vat):
                raise UserError(
                    'Define VAT or Fiscalcode for customer {name}'.format(
                        name=self.partner_id.name))
        return super().write(values)

    @api.multi
    @api.depends('is_customer_invoice')
    def _get_customer_number_identifier(self):
        for invoice in self:
            invoice.customer_number_identifier = '.1' \
                if invoice.is_customer_invoice else ''

    @api.multi
    def action_move_create(self):
        res = super().action_move_create()
        for invoice in self:
            if invoice.is_customer_invoice and \
                    not invoice.move_name.endswith('.1'):
                complete_number = '{number}.1'.format(
                    number=invoice.move_name)
                invoice.move_name = complete_number
                invoice.move_id.name = complete_number
            elif not invoice.is_customer_invoice and \
                    invoice.move_name.endswith('.1'):
                complete_number = invoice.move_name[:-2]
                invoice.move_name = complete_number
                invoice.move_id.name = complete_number
        return res


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    invoice_date = fields.Date(
        string="Invoice Date",
        related="invoice_id.date_invoice",
        store=True
    )

    price_compute_tax = fields.Float(
        string="Total",
        store=True,
        compute="_compute_tax_price",
        digits=dp.get_precision('Product Price')
    )

    tax_value = fields.Float(
        string="VAT Amount",
        store=True,
        compute="_compute_tax_price",
        digits=dp.get_precision('Product Price')
    )

    @api.multi
    @api.depends('product_id', 'price_unit', 'invoice_line_tax_ids',
                 'quantity')
    def _compute_tax_price(self):
        for line in self:
            result = line.invoice_line_tax_ids.compute_all(
                line.price_unit * line.quantity)
            line.tax_value = \
                result['total_included'] - result['total_excluded']
            line.price_compute_tax = result['total_included']
