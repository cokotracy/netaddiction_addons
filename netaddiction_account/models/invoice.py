# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import float_compare, float_round
import openerp.addons.decimal_precision as dp

class Invoice(models.Model):
    _inherit = "account.invoice"

    is_customer_invoice = fields.Boolean(strong="È una Fattura?")

    @api.multi
    def invoice_validate(self):
        res = super(Invoice,self).invoice_validate()
        if self.is_customer_invoice:
            self.number = self.number.strip() + '.1'
        return res


    @api.multi
    def write(self,values):
    	#se viene flaggato o deflaggato is_customer_invoice e il journal_id è = 1 (identifica fattura cliente)
        if 'is_customer_invoice' in values:
        	#se non c'è il fiscalcode allora rimando un errore e rimetto il vecchio nome fattura e is_customer_invoci è False
        	#altrimenti procedo al cambio di nome
            if self.partner_id.fiscalcode or self.partner_id.vat:
                if values.get('number', ''):
                    if values['is_customer_invoice']:
                        values['number'] = self.number.strip() + '.1'
                    else:
                        values['number'] = self.number.replace('.1','')
            else:
                if values.get('number', ''):
                    values['number'] = self.number.replace('.1','')
                values['is_customer_invoice'] = False
                raise ValidationError('Il Cliente non ha un codice Fiscale/Partita Iva')

        return super(Invoice,self).write(values)

    #per magazzino , resi , liste

    choose_wave_id = fields.Many2one(string="Lista",comodel_name="stock.picking.wave")
    create_credit_note = fields.Boolean(string="Crea una nota di credito")

    @api.model
    def create(self,values):
        if 'create_credit_note' in values:
            if values['create_credit_note']:
                values['type'] = 'in_refund'

        return super(Invoice,self).create(values)

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

            #se non è una lista di carico è una lista di reso
            if len(lines) == 0:
                results = self.env['stock.move'].search([('picking_id.wave_id','=',self.choose_wave_id.id)])
                for r in results:
                    for line in r.quant_ids:
                        taxes = line.product_id.supplier_taxes_id
                        invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
                        data = {
                            'name': line.name,
                            'origin': r.name,
                            'uom_id': line.product_id.uom_id.id,
                            'product_id': line.product_id.id,
                            'account_id': self.env['account.invoice.line'].with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                            'price_unit': (line.inventory_value/line.qty),
                            'discount': 0.0,
                            'quantity' : line.qty,
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

class InvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    price_compute_tax = fields.Float(string="Totale",store=True, compute="_compute_tax_price",digits_compute= dp.get_precision('Product Price'))
    tax_value = fields.Float(string="Prezzo Imposta",store=True, compute="_compute_tax_price",digits_compute= dp.get_precision('Product Price')) 
    invoice_date = fields.Date(string="Data Fattura", related="invoice_id.date_invoice", store=True)

    @api.one
    @api.depends('product_id','price_unit','invoice_line_tax_ids','quantity')
    def _compute_tax_price(self):
        result = self.invoice_line_tax_ids.compute_all(self.price_unit * self.quantity)

        self.tax_value = result['total_included'] - result['total_excluded']
        self.price_compute_tax = result['total_included']
