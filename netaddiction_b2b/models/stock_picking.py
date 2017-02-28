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
        
        term_id = int(orders[0].partner_id.payment_term_id.id)
        
        pick_id = False
        delivery_barcode = False
        carrier = False
        for sp in stock_picking_list:
            if not pick_id:
                pick_id = sp.id
            if not delivery_barcode:
                delivery_barcode = sp.delivery_barcode
            if not carrier:
                carrier = sp.carrier_id
            
            sp.write({'delivery_barcode' : delivery_barcode, 'carrier_tracking_ref' : delivery_barcode, 'carrier_id' : carrier.id})


        invoice_vals = {
            'name': orders[0].client_order_ref or '',
            'origin': ', '.join(names),
            'type': 'out_invoice',
            'reference': ', '.join(names),
            'account_id': orders[0].partner_invoice_id.property_account_receivable_id.id,
            'partner_id': orders[0].partner_invoice_id.id,
            'shipping_address' : orders[0].partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': orders[0].pricelist_id.currency_id.id,
            'comment': orders[0].note,
            'payment_term_id': term_id,
            'fiscal_position_id': orders[0].fiscal_position_id.id or orders[0].partner_invoice_id.property_account_position_id.id,
            'company_id': orders[0].company_id.id,
            'user_id': orders[0].user_id and orders[0].user_id.id,
            'team_id': orders[0].team_id.id,
            'is_customer_invoice' : True,
            'pick_id' : pick_id,
        }

        invoice = self.env["account.invoice"].create(invoice_vals)
        
        for sp in stock_picking_list:
            for sm in sp.move_lines:
                ls = [sl for sl in sp.sale_id.order_line if sl.product_id.id ==sm.product_id.id]
                if ls:
                    l = ls[0].invoice_line_create(invoice.id, sm.product_uom_qty)
            
        #aggiungo spese di spedizione 
        acc = self.env.ref('l10n_it.3101')   
        carrier_price = orders[0].pricelist_id.carrier_price
        gratis = orders[0].pricelist_id.carrier_gratis
        total = 0
        for line in invoice.invoice_line_ids:
            total += (line.price_unit*line.quantity)

        if total >= gratis:
            carrier_price = 0
        res = {
            'name': carrier.product_id.display_name,
            'account_id': acc.id,
            'price_unit': carrier_price,
            'quantity': 1,
            'uom_id': carrier.product_id.uom_id.id,
            'product_id': carrier.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, [carrier.product_id.taxes_id.id])],
            'invoice_id' : invoice.id
        }
        self.env['account.invoice.line'].create(res)

        invoice.state= 'draft'
        invoice.compute_taxes()

        mail = {
            'subject': 'Fattura Accompagnatoria B2B %s' % (invoice.name),
            'email_from': 'shopping@multiplayer.com',
            'reply_to': 'shopping@multiplayer.com',
            'email_to': 'valeria.risoldi@netaddiction.it',
            'email_cc': 'matteo.piciucchi@netaddiction.it,riccardo.ioni@netaddiction.it,andrea.alunni@netaddiction.it',
            'body_html': 'Emettere fattura accompagnatoria: <br/><a href="https://backoffice.netaddiction.it/web#id='+str(invoice.id)+'&view_type=form&model=account.invoice">Link Fattura</a>',
            'model':'account.invoice',
            'res_id':invoice.id
        }
        email = self.env['mail.mail'].create(mail)
        email.send()
        return invoice
