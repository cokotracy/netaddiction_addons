from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto import Random

from openerp import models, fields, api
import cypher



class PaypalConfiguration(models.TransientModel):
    
    _name = "netaddiction.paypal.settings"
    _inherit = 'res.config.settings'

    username = fields.Char(string='Username', required=True, help="Paypal Username")
    password = fields.Char(string='password', required=True, help="Paypal Password")
    signature = fields.Char(string='Signature', required=True, help="The Paypal secret key")
    
   

    

    @api.one
    def set_username(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.username)
        self.env["ir.values"].search([("name","=","paypal_username")]).value = res


    @api.one
    def set_password(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.password)
        self.env["ir.values"].search([("name","=","paypal_password")]).value = res
        

    @api.one
    def set_signature(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","paypal.key")]).value
        res = cypher.encrypt(key,self.signature)
        self.env["ir.values"].search([("name","=","paypal_signature")]).value = res
        


        
        