# -*- coding: utf-8 -*-

from openerp import models


class GiftInvoiceHelper(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con PayPal
    """
    _name = "netaddiction.gift_invoice_helper"

    def add_gift_to_invoices(self, order, inv_lst):
        tot_gift = order.gift_discount
        if tot_gift <= 0.0:
            return

        for inv in inv_lst:
            print tot_gift, order.amount_total, inv.amount_total
            gift_value = self.compute_gift_value(tot_gift, order.amount_total, inv.amount_total)
            print gift_value
            self.gift_to_invoice(gift_value, inv)

    def gift_to_invoice(self, value, inv):

        gift_pid = self.env['ir.model.data'].search([('name', '=', 'product_gift')]).res_id
        gp = self.env['product.product'].search([('id', '=', gift_pid)])

        value_neg = 0 - value
        account_id = self.env['account.account'].search([('code', '=', 310100), ('company_id', '=', 1)])
        invoice_line = {
            'product_id': gift_pid,
            'quantity': 1,
            'price_unit': float(value_neg),
            'name': 'Gift',
            'account_id': account_id.id,
            'invoice_line_tax_ids': [(6, False, [gp.taxes_id.id])],
        }
        inv.write({'invoice_line_ids': [(0, 0, invoice_line)]})
        inv.compute_taxes()
        inv._compute_amount()

    def compute_gift_value(self, tot_gift, tot_order, tot_invoice):
        return(tot_invoice * tot_gift) / (tot_gift + tot_order)
