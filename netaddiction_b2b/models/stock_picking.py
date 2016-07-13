# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def invoice_single(self, stock_picking_list,partner_id):
    	"""
    	crea una fattura per tutte le stock line in 'stock_picking_list' e la collega ai rispettivi ordini
    	'partner_id' id del partner
    	"""
    	if not stock_picking_list or not partner_id:
    		return False
    	journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
        	raise UserError(_('Please define an accounting sale journal for this company.'))
        orders = [sp.sale_id for sp in stock_picking_list]
        if not orders:
        	return False
        names = [so.name for so in orders]
 
        invoice_vals = {
        	'name': orders[0].client_order_ref or '',
            'origin': ', '.join(names),
            'type': 'out_invoice',
            'reference': ', '.join(names),
            'account_id': orders[0].partner_invoice_id.property_account_receivable_id.id,
            'partner_id': partner_id,
            'journal_id': journal_id,
            'currency_id': orders[0].pricelist_id.currency_id.id,
            'comment': orders[0].note,
            'payment_term_id': orders[0].payment_term_id.id,
            'fiscal_position_id': orders[0].fiscal_position_id.id or orders[0].partner_invoice_id.property_account_position_id.id,
            'company_id': orders[0].company_id.id,
            'user_id': orders[0].user_id and orders[0].user_id.id,
            'team_id': orders[0].team_id.id,
            'is_customer_invoice' : True,
        }

        invoice = self.env["account.invoice"].create(invoice_vals)
        print invoice
    	for sp in stock_picking_list:
    		for sm in sp.move_lines:
    			ls = [sl for sl in sp.sale_id.order_line if sl.product_id.id ==sm.product_id.id]
    			if ls:
    				ls[0].invoice_line_create(invoice.id, sm.product_uom_qty)
    	
    	invoice.state= 'open'
    	return invoice
