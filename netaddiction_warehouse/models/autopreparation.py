# -*- coding: utf-8 -*-
from openerp.exceptions import Warning
from openerp import models, fields, api
from openerp.tools import float_compare, float_is_zero

class autopreparation(models.TransientModel):

    _inherit = "stock.picking.to.wave"

    @api.multi 
    def attach_pickings(self, values):
        #versione base, metto in lista le spedizioni segnate
        stocks = self.env['stock.picking'].search([('id','in',values['active_ids'])])
        error_stock = []
        for stock in stocks:
            # se non è disponibile
            if stock.state != 'assigned':
                error_stock.append(stock.id)
            #se ha già una lista
            if len(stock.wave_id) > 0:
                error_stock.append(stock.id)
            #se non è in lavorazione o in parzialmente completato
            if stock.sale_id.state not in ['sale','partial_done']:
                error_stock.append(stock.id)
            #controllo i pagamenti
            if stock.sale_id.payment_method_id is False:
                error_stock.append(stock.id)
            cc_payment = self.env.ref('netaddiction_payments.cc_journal')
            if stock.sale_id.payment_method_id == cc_payment:
                list_payments = []
                for payment in stock.sale_id.account_payment_ids:
                    if float_compare(round(payment.amount,2),round(stock.total_import,2),2) == 0:
                        list_payments.append(payment)

                if len(list_payments) >= 1:
                    for p in list_payments:
                        if p.state == 'draft' and p.cc_status != 'commit':
                            try:
                                p.auth_and_check(p.partner_id,p.partner_id.email,p.amount,p.cc_token,p.order_id)
                            except Exception:
                                error_stock.append(stock.id)
                            break
                else:
                    error_stock.append(stock.id)

        if len(error_stock) > 0:
            view_id = self.env['ir.ui.view'].search([('name','=','stock.vpicktree')])
            action = {
                'type': 'ir.actions.act_window',
                'res_model': "stock.picking",
                'view_id': view_id.id,
                'view_mode': 'tree,form',
                'target': 'current',
                'domain' : [('id','in',error_stock)],
                'context': {},
                'name' : 'Spedizioni con Errori'
            }
            return action
       
        stocks.write({'wave_id' : self.wave_id.id })
        #self.env.cr.commit()
