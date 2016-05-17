from openerp import models, fields, api
import cypher



class PositivityConfiguration(models.TransientModel):
    
    _name = "netaddiction.positivity.settings"
    _inherit = 'res.config.settings'

    tid = fields.Char(string='Tid', required=True)
    kSig = fields.Char(string='kSig', required=True)
    tid_MOTO = fields.Char(string='Tid MOTO', required=True)
    kSig_MOTO = fields.Char(string='kSig MOTO', required=True)

    

    @api.one
    def set_tid(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        res = cypher.encrypt(key,self.tid)
        self.env["ir.values"].search([("name","=","positivity_tid")]).value = res


    @api.one
    def set_kSig(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        res = cypher.encrypt(key,self.kSig)
        self.env["ir.values"].search([("name","=","positivity_kSig")]).value = res


    @api.one
    def set_tid_MOTO(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        res = cypher.encrypt(key,self.tid_MOTO)
        self.env["ir.values"].search([("name","=","positivity_tid_MOTO")]).value = res


    @api.one
    def set_kSig_MOTO(self, values):
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        res = cypher.encrypt(key,self.kSig_MOTO)
        self.env["ir.values"].search([("name","=","positivity_kSig_MOTO")]).value = res


