
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto import Random

from openerp import models, fields, api
import cypher



class SofortConfiguration(models.TransientModel):
    
    _name = "netaddiction.sofort.settings"
    _inherit = 'res.config.settings'

    username = fields.Char(string='Username', required=True, help="Sofort Username")
    apikey = fields.Char(string='Api key', required=True, help="Sofort Api Key")
    project = fields.Char(string='Project', required=True, help="Sofort Project")
    
   

    

    @api.one
    def set_username(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","sofort.key")]).value
        res = cypher.encrypt(key,self.username)
        self.env["ir.values"].search([("name","=","sofort_username")]).value = res


    @api.one
    def set_password(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","sofort.key")]).value
        res = cypher.encrypt(key,self.apikey)
        self.env["ir.values"].search([("name","=","sofort_apikey")]).value = res
        

    @api.one
    def set_project(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","sofort.key")]).value
        res = cypher.encrypt(key,self.project)
        self.env["ir.values"].search([("name","=","sofort_project")]).value = res
        


        
        