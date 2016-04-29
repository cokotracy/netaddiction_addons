# -*- coding: utf-8 -*-

from openerp import models, fields, api
import cypher
import paypal




class PaypalExecutor(models.TransientModel):
    _name = "netaddiction.paypal.executor"

    @api.one
    def express_checkout(self):
        encripted_username = self.env["ir.values"].search([("name","=","paypal_username")]).value
        encripted_password = self.env["ir.values"].search([("name","=","paypal_password")]).value
        encripted_signature = self.env["ir.values"].search([("name","=","paypal_signature")]).value
        encripted_email = self.env["ir.values"].search([("name","=","paypal_email")]).value
    
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value

        print cypher.decrypt(key,encripted_username)
        print cypher.decrypt(key,encripted_password)
        print cypher.decrypt(key,encripted_signature)
        print cypher.decrypt(key,encripted_email)
        
     #    enc = self.env["ir.values"].search([("name","=","paypal_username")]).value
     #    print enc
     #    username = aes.decrypt(enc)
     #    password = aes.decrypt(self.env["ir.values"].search([("name","=","paypal_password")]).value)
     #    signature = aes.decrypt(self.env["ir.values"].search([("name","=","paypal_signature")]).value)
     #    email = aes.decrypt(self.env["ir.values"].search([("name","=","paypal_email")]).value)
    	# config = PayPalConfig(API_USERNAME=username,
     #                  API_PASSWORD=password,
     #                  API_SIGNATURE=signature)
    	# print self.config