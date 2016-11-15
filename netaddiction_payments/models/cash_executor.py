# -*- coding: utf-8 -*-

from openerp import models, fields, api
import payment_exception




class CashExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti ricevuti in contanti
    """
    _name = "netaddiction.cash.executor"

    @api.one
    def register_cash_payment(self,user_id, amount, order_id):
        cash_journal = self.env['account.journal'].search([('code','=','CSH1')])
        pay_inbound = self.env["account.payment.method"].search([("payment_type","=","inbound")])
        pay_inbound = pay_inbound[0] if isinstance(pay_inbound,list) else pay_inbound
        order = self.env["sale.order"].search([("id","=",order_id)])
        if not order:
            raise payment_exception.PaymentException(payment_exception.CASH,"order id non valido! %s" %order_id)
        if cash_journal and pay_inbound:
            if order.state == 'draft':
                order.action_confirm()

            if order.state in ('sale', 'problem'):
                name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
          
               
                payment = self.env["account.payment"].create({"partner_type" : "customer", "partner_id" : user_id, "journal_id" : cash_journal.id, "amount" : amount, "order_id" : order_id, "state" : 'draft', "payment_type" : 'inbound', "payment_method_id" : pay_inbound.id, "name" : name, 'communication' : order.name,  })

                order.payment_method_id = cash_journal.id

            

                self._set_order_to_invoice(order)

                inv_lst = order.action_invoice_create()

                payment.invoice_ids = [(4, inv, None) for inv in inv_lst]

                for inv_id in inv_lst:
                    inv = self.env["account.invoice"].search([("id","=",inv_id)])
                    inv.signal_workflow('invoice_open')
                    # inv.payement_id = [(6, 0, [payment.id])]

                payment.delay_post()

                #assegno il pagamento alle spedizioni
                for delivery in order.picking_ids: 
                    delivery.payment_id = payment.id       

                return 1

            else:
                raise payment_exception.PaymentException(payment_exception.CASH,"problema con l'ordine %s" % order.id) 
        else:
            raise payment_exception.PaymentException(payment_exception.CASH,"impossibile trovare metodo di pagamento cash") 

    @api.one
    def _set_order_to_invoice(self,order):
        for line in order.order_line:
            line.qty_to_invoice = line.product_uom_qty
