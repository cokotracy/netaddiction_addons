# -*- coding: utf-8 -*-


from float_compare import isclose
from openerp import api, models, fields

import payment_exception


class ZeroPaymentExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamento a costo zero
    """
    _name = "netaddiction.zeropayment.executor"


    def set_order_zero_payment(self,order, real_invoice=False):
        if not order:
            raise payment_exception.PaymentException(payment_exception.ZERO,"order id non valido! %s" %order.id)

        if not isclose(order.amount_total,0.0000,abs_tol=0.009):
            raise payment_exception.PaymentException(payment_exception.ZERO,"ordine non a 0! pagamento dovuto: % s" % order.amount_total)

        zeropayment_journal  = self.env['ir.model.data'].get_object('netaddiction_payments','zeropay_journal')
        order.payment_method_id = zeropayment_journal.id

        if order.state == 'draft':
            order.action_confirm()

        if order.state == 'sale':
            
            if not isclose(order.amount_total,0.0000,abs_tol=0.009):
                #TODO spostare in problema e commentare?
                raise payment_exception.PaymentException(payment_exception.ZERO,"ordine non a 0! pagamento dovuto di spedizione: % s" % order.amount_total)

            inv_lst = []


            for line in order.order_line:
                #resetto la qty_to_invoice di tutte le linee
                line.qty_to_invoice = 0
            for delivery in order.picking_ids:                    
                for stock_move in delivery.move_lines_related:
                    self._set_order_to_invoice(stock_move,order)

                self._set_delivery_to_invoice(delivery,order)

                inv_lst += order.action_invoice_create()

            for inv in inv_lst:
                invoice = self.env['account.invoice'].search([("id","=",inv)])
                invoice.signal_workflow('invoice_open')
                invoice.is_customer_invoice = real_invoice

    def _set_order_to_invoice(self,stock_move,order):
        """dato 'order' imposta qty_to_invoice alla quantità giusta solo per i prodotti che si trovano in 'stock_move'
        """
        prod_id = stock_move.product_id
        qty = stock_move.product_uom_qty

        lines = [line for line in order.order_line if line.product_id == prod_id ]
        for line in lines:
            qty_to_invoice = qty if qty < line.product_uom_qty else line.product_uom_qty

            line.qty_to_invoice += qty_to_invoice

            qty = qty - qty_to_invoice

            if qty <= 0:
                break

    def _set_delivery_to_invoice(self,pick,order):
        """dato 'order' imposta qty_to_invoice per una spedizione 
        """
        lines = [line for line in order.order_line if line.is_delivery and line.price_unit == pick.carrier_price and  line.qty_invoiced < line.product_uom_qty]

        if lines:
            lines[0].qty_to_invoice = 1

