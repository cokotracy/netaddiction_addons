# -*- coding: utf-8 -*-
from openerp import models, fields, api

class GrouponConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'netaddiction.groupon.config'

    groupon_customer_id = fields.Integer(string="Id utente Groupon")

    groupon_carrier_sku = fields.Integer(string="Id Corriere")

    @api.one
    def set_groupon_customer_id(self, values):
        self.env['ir.values'].search([("name", "=", "groupon_customer_id"), ("model", "=", "groupon.config")]).value = self.groupon_customer_id

    @api.model
    def get_default_groupon_customer_id(self, fields):
        return {'groupon_customer_id': int(self.env['ir.values'].search([("name", "=", "groupon_customer_id"), ("model", "=", "groupon.config")]).value)}

    @api.one
    def set_groupon_carrier_sku(self, values):
        self.env['ir.values'].search([("name", "=", "groupon_carrier_sku"), ("model", "=", "groupon.config")]).value = self.groupon_carrier_sku

    @api.model
    def get_default_groupon_carrier_sku(self, fields):
        return {'groupon_carrier_sku': int(self.env['ir.values'].search([("name", "=", "groupon_carrier_sku"), ("model", "=", "groupon.config")]).value)}
