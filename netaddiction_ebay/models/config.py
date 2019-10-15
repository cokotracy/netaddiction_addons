# -*- coding: utf-8 -*-
from openerp import models, fields, api

class EbayConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'netaddiction.ebay.config'

    paypal_account = fields.Char(string="Account Paypal su cui ricevere pagamenti ebay")
    max_num_retry = fields.Integer(string="Numero massimo di richieste di job status da fare a ebay", default=20)

    @api.one
    def set_paypal_account(self, values):
        self.env['ir.values'].search([("name", "=", "paypal_account"), ("model", "=", "netaddiction.ebay.config")]).value = self.paypal_account

    @api.one
    def set_max_num_retry(self, values):
        self.env['ir.values'].search([("name", "=", "paypal_account"), ("model", "=", "netaddiction.ebay.config")]).value = self.max_num_retry
