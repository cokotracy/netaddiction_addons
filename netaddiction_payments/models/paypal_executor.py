# -*- coding: utf-8 -*-

from openerp import models, fields, api
import cypher
import paypal




class PaypalExecutor(models.TransientModel):
    _name = "netaddiction.paypal.executor"

    token = fields.Char()




    @api.one
    def get_express_checkout_link(self,amount):
        encripted_username = self.env["ir.values"].search([("name","=","paypal_username")]).value
        encripted_password = self.env["ir.values"].search([("name","=","paypal_password")]).value
        encripted_signature = self.env["ir.values"].search([("name","=","paypal_signature")]).value
        
    
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value

        username = cypher.decrypt(key,encripted_username)
        password = cypher.decrypt(key,encripted_password)
        signature = cypher.decrypt(key,encripted_signature)
        email = "andrea.bozzi-buyer@netaddiction.it"

        #TODO: API_ENVIRONMENT = 'PRODUCTION'
        config = paypal.PayPalConfig(API_USERNAME=username,
                      API_PASSWORD=password,
                      API_SIGNATURE=signature)
        pp_interface = paypal.PayPalInterface(config= config)

        setexp_response = pp_interface.set_express_checkout(
            amt=amount,
            returnurl='http://www.paypal.com', cancelurl='http://www.ebay.com',
            paymentaction='Sale',
            email=email, currencycode='EUR'
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

    @api.one
    def finalize_payment(self,amount):
        encripted_username = self.env["ir.values"].search([("name","=","paypal_username")]).value
        encripted_password = self.env["ir.values"].search([("name","=","paypal_password")]).value
        encripted_signature = self.env["ir.values"].search([("name","=","paypal_signature")]).value
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        username = cypher.decrypt(key,encripted_username)
        password = cypher.decrypt(key,encripted_password)
        signature = cypher.decrypt(key,encripted_signature)
        email = "andrea.bozzi-buyer@netaddiction.it"

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
            print pp_interface.do_express_checkout_payment(token=self.token, amt=amount, paymentaction='Sale',payerid=payer_id,currencycode='EUR')



        
