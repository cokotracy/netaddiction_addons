from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto import Random

from openerp import models, fields, api
import cypher

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class PaypalConfiguration(models.TransientModel):
    _name = "netaddiction.paypal.settings"
    _inherit = 'res.config.settings'

    username = fields.Char(string='Username', required=True, help="Paypal Username")
    password = fields.Char(string='password', required=True, help="Paypal Password")
    signature = fields.Char(string='Signature', required=True, help="The Paypal secret key")
    email = fields.Char(string='Email', required=True, help="Paypal email")
   

    

    @api.one
    def set_username(self, values):
        print "-----USERNAME----"
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.username)
        print res
        self.env["ir.values"].search([("name","=","paypal_username")]).value = res


    @api.one
    def set_password(self, values):
        print "-----PASSWORD----"
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.password)
        print res
        self.env["ir.values"].search([("name","=","paypal_password")]).value = res
        

    @api.one
    def set_signature(self, values):
        print "-----SIGNATURE----"
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.signature)
        print res
        self.env["ir.values"].search([("name","=","paypal_signature")]).value = res
        

    @api.one
    def set_email(self, values):
        print "-----EMAIL----"
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.email)
        print res
        self.env["ir.values"].search([("name","=","paypal_email")]).value = res
        
        