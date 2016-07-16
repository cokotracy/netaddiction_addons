# -*- coding: utf-8 -*-

from openerp import models, fields, api
import cypher
import paypal
import payment_exception


PAYMENTACTION = 'Sale'
CUR = 'EUR'



class PaypalExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con PayPal
    """
    _name = "netaddiction.paypal.executor"

    token = fields.Char()




    @api.one
    def get_express_checkout_link(self,amount,returnurl,cancelurl,email):
        """ Primo metodo da chiamare per effettuare un pagamento su paypal
            Parametri:
            -amount: quantità da pagare, IMPORTANTE: COMPRESE SPESE DI SPEDIZIONE
            -returnurl: url a cui reindirizzare l'utente in caso di successo nel pagamento expres_checkout
            -cancelurl: url a cui reindirizzare l'utente in caso di fallimento nel pagamento expres_checkout
            -email: email del cliente
            Returns:
            -se tutto ok: il link per l'expres_checkout
            -se fallisce set_express_checkout: raise PaymentException
            -se fallisce get_express_checkout_details: raise PaymentException
            Raise PayPalError: propaga i raise dell'interfaccia di paypal
        """
        encripted_username = self.env["ir.values"].search([("name","=","paypal_username")]).value
        encripted_password = self.env["ir.values"].search([("name","=","paypal_password")]).value
        encripted_signature = self.env["ir.values"].search([("name","=","paypal_signature")]).value
        
    
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value

        username = cypher.decrypt(key,encripted_username)
        password = cypher.decrypt(key,encripted_password)
        signature = cypher.decrypt(key,encripted_signature)
       

        #TODO: API_ENVIRONMENT = 'PRODUCTION'
        config = paypal.PayPalConfig(API_USERNAME=username,
                      API_PASSWORD=password,
                      API_SIGNATURE=signature)
        pp_interface = paypal.PayPalInterface(config= config)

        setexp_response = pp_interface.set_express_checkout(
            amt=amount,
            returnurl=returnurl, cancelurl=cancelurl,
            paymentaction=PAYMENTACTION,
            email=email, currencycode=CUR
        )

        if setexp_response and setexp_response.success:

            self.token = setexp_response.token
            getexp_response = pp_interface.get_express_checkout_details(token=self.token)

            if getexp_response and getexp_response.success:
                
                return pp_interface.generate_express_checkout_redirect_url(self.token)
                
            else:
                raise payment_exception.PaymentException(payment_exception.PAYPAL,"fallito il get_express_checkout_details") 
        else:
            raise payment_exception.PaymentException(payment_exception.PAYPAL,"fallito il set_express_checkout in get_express_checkout_link")

    @api.one
    def finalize_payment(self,amount,user_id,order_id):
        """ Secondo metodo da chiamare per effettuare un pagamento su paypal, finalizza il pagamento
            e genera l'oggetto di tipo "account.payment" da associare all'ordine
            Parametri:
            -amount: quantità da pagare
            -user_id: id su odoo dell'utente che deve pagare
            -order_id: id su odoo dell'ordine associato al pagamento
            
            Returns:
            -se tutto ok: 1
            -se fallisce do_express_checkout_payment: raise PaymentException
            -se fallisce get_express_checkout_details: raise PaymentException
            -se fallisce la registrazione del pagamento su odoo ma il pagamento paypal va a buon fine: -3
            Raise PayPalError: propaga i raise dell'interfaccia di paypal
        """
        encripted_username = self.env["ir.values"].search([("name","=","paypal_username")]).value
        encripted_password = self.env["ir.values"].search([("name","=","paypal_password")]).value
        encripted_signature = self.env["ir.values"].search([("name","=","paypal_signature")]).value
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        username = cypher.decrypt(key,encripted_username)
        password = cypher.decrypt(key,encripted_password)
        signature = cypher.decrypt(key,encripted_signature)
       

        #TODO: API_ENVIRONMENT = 'PRODUCTION'
        config = paypal.PayPalConfig(API_USERNAME=username,
                      API_PASSWORD=password,
                      API_SIGNATURE=signature)
        pp_interface = paypal.PayPalInterface(config= config)
        getexp_response = pp_interface.get_express_checkout_details(token=self.token)
        if getexp_response and getexp_response.success:
            

            try:
                payer_id = getexp_response.payerid
            except AttributeError:
                #se non c'è il payerid nella risposta vuol dire che il cliente non ha completato il pagamento
                raise payment_exception.PaymentException(payment_exception.PAYPAL,"il cliente non ha completato il pagamento")

            
            payment_response = pp_interface.do_express_checkout_payment(token=self.token, amt=amount, paymentaction=PAYMENTACTION,payerid=payer_id,currencycode=CUR)
            
            
            if payment_response and payment_response.success:
                #save on odoo
                return self._register_payment(user_id,payment_response.amt,order_id,payment_response.paymentinfo_0_transactionid)
                
            else:
                raise payment_exception.PaymentException(payment_exception.PAYPAL,"fallito il register_payment") 
        else:
            raise payment_exception.PaymentException(payment_exception.PAYPAL,"fallito il get_express_checkout_details in finalize_payment") 


    @api.one
    def _register_payment(self,user_id, amount, order_id,transaction_id):
        pp_aj = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal')
        pay_inbound = self.env["account.payment.method"].search([("payment_type","=","inbound")])
        pay_inbound = pay_inbound[0] if isinstance(pay_inbound,list) else pay_inbound
        if pp_aj and pay_inbound:
            name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
            pp_id = pp_aj.id
            order = self.env["sale.order"].search([("id","=",order_id)])
            payment = self.env["account.payment"].create({"partner_type" : "customer", "partner_id" : user_id, "journal_id" : pp_id, "amount" : amount, "order_id" : order_id, "state" : 'draft', "payment_type" : 'inbound', "payment_method_id" : pay_inbound.id, "name" : name, 'communication' : order.name, 'paypal_transaction_id': transaction_id,  })

            order.payment_method_id = pp_aj.id
            order.action_confirm()

            self._set_order_to_invoice(order)

            inv_lst = order.action_invoice_create()

            payment.invoice_ids = [(4, inv, None) for inv in inv_lst]

            for inv_id in inv_lst:
                inv = self.env["account.invoice"].search([("id","=",inv_id)])
                inv.signal_workflow('invoice_open')
                # inv.payement_id = [(6, 0, [payment.id])]

            payment.post()

            return 1
        else:
            raise payment_exception.PaymentException(payment_exception.PAYPAL,"impossibile trovare il metodo di pagamento PayPal")
        

    @api.one
    def _set_order_to_invoice(self,order):
        for line in order.order_line:
            line.qty_to_invoice = line.product_uom_qty




        
