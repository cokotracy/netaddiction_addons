# -*- coding: utf-8 -*-

from openerp import models, fields, api
from collections import defaultdict
from datetime import datetime,date,timedelta
from openerp.tools.float_utils import float_compare

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    choose_wave_id = fields.Many2one(string="Lista di carico",comodel_name="stock.picking.wave")

    @api.onchange('state', 'partner_id', 'invoice_line_ids')
    def _onchange_allowed_purchase_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        purchase_line_ids = self.invoice_line_ids.mapped('purchase_line_id')
        purchase_ids = self.invoice_line_ids.mapped('purchase_id').filtered(lambda r: r.order_line <= purchase_line_ids)

        result['domain'] = {'purchase_id': [
            ('state', '<>', 'draft'),
            ('partner_id', '=', self.partner_id.id),
            ('id', 'not in', purchase_ids.ids),
            ],
            'choose_wave_id' :[
            ('state', '=' ,'done'),
            ('picking_ids.partner_id','=',self.partner_id.id)
            ]}
        return result

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line:
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('purchase_line_id'):
                continue
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0

            if qty > 0.0:
                taxes = line.taxes_id or line.product_id.supplier_taxes_id
                invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
                data = {
                    'purchase_line_id': line.id,
                    'name': line.name,
                    'origin': self.purchase_id.origin,
                    'uom_id': line.product_uom.id,
                    'product_id': line.product_id.id,
                    'account_id': self.env['account.invoice.line'].with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                    'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id),
                    'quantity': qty,
                    'discount': 0.0,
                    'account_analytic_id': line.account_analytic_id.id,
                    'invoice_line_tax_ids': invoice_line_tax_ids.ids
                }
                account = new_lines.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
                if account:
                    data['account_id'] = account.id
                new_line = new_lines.new(data)
                new_line._set_additional_fields(self)
                new_lines += new_line

        self.invoice_line_ids += new_lines
        self.purchase_id = False
        return {}

    @api.onchange('choose_wave_id')
    def picking_ids_purchase_order_change(self):
        if not self.choose_wave_id:
            return {}

        new_lines = self.env['account.invoice.line']
        for pick in self.choose_wave_id.picking_ids:
            lines = self.env['purchase.order'].search([('name','=',pick.origin)])
            for l in lines:
                for line in l.order_line:
                    # Load a PO line only once
                    if line in self.invoice_line_ids.mapped('purchase_line_id'):
                        continue
                    if line.product_id.purchase_method == 'purchase':
                        qty = line.product_qty - line.qty_invoiced
                    else:
                        qty = line.qty_received - line.qty_invoiced
                    if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                        qty = 0.0

                    if qty > 0.0:
                        taxes = line.taxes_id or line.product_id.supplier_taxes_id
                        invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
                        data = {
                            'purchase_line_id': line.id,
                            'name': line.name,
                            'origin': self.purchase_id.origin,
                            'uom_id': line.product_uom.id,
                            'product_id': line.product_id.id,
                            'account_id': self.env['account.invoice.line'].with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                            'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id),
                            'quantity': qty,
                            'discount': 0.0,
                            'account_analytic_id': line.account_analytic_id.id,
                            'invoice_line_tax_ids': invoice_line_tax_ids.ids
                        }
                        account = new_lines.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
                        if account:
                            data['account_id'] = account.id
                        new_line = new_lines.new(data)
                        new_line._set_additional_fields(self)
                        new_lines += new_line

        self.invoice_line_ids += new_lines
        self.purchase_id = False
        return {}

            