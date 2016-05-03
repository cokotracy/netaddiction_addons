# -*- coding: utf-8 -*-

from openerp import models, fields, api
import cypher
import paypal


PAYMENTACTION = 'Sale'
CUR = 'EUR'

class PaypalExecutor(models.TransientModel):
    _name = "netaddiction.paypal.executor"

    token = fields.Char()




    @api.one
    def get_express_checkout_link(self,amount,returnurl,cancelurl,email):
        encripted_username = self.env["ir.values"].search([("name","=","paypal_username")]).value
        encripted_password = self.env["ir.values"].search([("name","=","paypal_password")]).value
        encripted_signature = self.env["ir.values"].search([("name","=","paypal_signature")]).value
        
    
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value

        username = cypher.decrypt(key,encripted_username)
        password = cypher.decrypt(key,encripted_password)
        signature = cypher.decrypt(key,encripted_signature)
        #email = "andrea.bozzi-buyer@netaddiction.it"

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

        if setexp_response and setexp_response['ACK'] == 'Success':

            print "------setexp_response--------"
            print setexp_response
            self.token = setexp_response.token
            getexp_response = pp_interface.get_express_checkout_details(token=self.token)

            if getexp_response and getexp_response['ACK'] == 'Success':
                print "------getexp_response--------"
                print getexp_response
                redirect_url = pp_interface.generate_express_checkout_redirect_url(self.token)
                print "------redirect_url--------"
                print redirect_url
            else:
                #TODO: return error
                pass
        else:
            #TODO: return error
            pass

    @api.one
    def finalize_payment(self,amount,user_id,order_id):
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
        if getexp_response and getexp_response['ACK'] == 'Success':
            print getexp_response
            payer_id = getexp_response['PAYERID']
            print "--------------FINALIZE------------"
            payment_response = pp_interface.do_express_checkout_payment(token=self.token, amt=amount, paymentaction='Sale',payerid=payer_id,currencycode='EUR')
            if payment_response and payment_response['ACK'] == 'Success':
                #todo: save on odoo
                self._register_payment(user_id,payment_response['AMT'],order_id)
                pass
            else:
                #TODO: return error
                pass
        else:
            #TODO: return error
            pass


    @api.one
    def _register_payment(self,user_id, amount, order_id):
        pp_aj = self.env["account.journal"].search([("name","=","Paypal")])
        pay_inbound = self.env["account.payment.method"].search([("payment_type","=","inbound")])
        pay_inbound = pay_inbound[0] if isinstance(pay_inbound,list) else pay_inbound
        print "HARE"
        if pp_aj and pay_inbound:
            name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today).next_by_code('account.payment.customer.invoice')
            pp_id = pp_aj.id
            self.env["account.payment"].create({"partner_type" : "customer", "partner_id" : user_id, "journal_id" : pp_id, "amount" : amount, "order_id" : order_id, "state" : 'posted', "payment_type" : 'inbound', "payment_method_id" : pay_inbound.id, "name" : name })
            print "HERE"
        





        
