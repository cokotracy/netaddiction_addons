from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto import Random

from openerp import models, fields, api
import cypher


class StripeConfiguration(models.TransientModel):

    _name = "netaddiction.stripe.settings"
    _inherit = 'res.config.settings'

    public_key = fields.Char(
        string='Public Key', required=True, help="Stripe Public Key")
    private_key = fields.Char(
        string='Private Key', required=True, help="Stripe Private Key")

    @api.one
    def set_public_key(self, values):
        key = self.env["ir.config_parameter"].search(
            [("key", "=", "stripe.key")]).value
        res = cypher.encrypt(key, self.public_key)
        self.env["ir.values"].search(
            [("name", "=", "stripe_public_key")]).value = res

    @api.one
    def set_private_key(self, values):
        key = self.env["ir.config_parameter"].search(
            [("key", "=", "stripe.key")]).value
        res = cypher.encrypt(key, self.private_key)
        self.env["ir.values"].search(
            [("name", "=", "stripe_private_key")]).value = res
