# -*- coding: utf-8 -*-

from openerp import models, fields, api

# configurazioni del plugin
class CustomerLoyaltyConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'customer.loyalty.settings'

    revenues_percentage = fields.Integer(string="Percentage of revenue",
        help="For each completed order the customer receives this percentage of revenue on the total order.")
    points_money = fields.Selection(selection=(('points', 'Points'), ('money', 'Money')),
        string="Points or Money revenues",
        help="Choose whether to receive points or money.")
    conversion_points_money = fields.Float(string="1 Point is equal to: (your currency)",
        help="Choose the value of one point.")

    def _get_all_order_state(self):
        return list(self.env['sale.order'].fields_get(allfields=['state'])['state']['selection'])

    order_state = fields.Selection(selection=_get_all_order_state,
        string="Order state",
        help="Choose which order status trigger revenue.")

    delay_days = fields.Integer(string="Days of delay to add revenue")
    welcome_points = fields.Float(string="Welcome Points")
    text_welcome = fields.Char(string="Text Welcome Points")
    text_fe = fields.Char(string="Name")

    @api.model
    def get_default_revenues_percentage(self, fields):
        value = self.env['ir.values'].search([("name", "=", "revenues_percentage"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'revenues_percentage': 0}

        return {'revenues_percentage': int(value.value)}

    @api.model
    def set_default_revenues_percentage(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "revenues_percentage"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = int(res.revenues_percentage)
            return True

        return self.env['ir.values'].create({'name': 'revenues_percentage', 'value': int(res.revenues_percentage), 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_points_money(self, fields):
        value = self.env['ir.values'].search([("name", "=", "points_money"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'points_money': False}

        return {'points_money': value.value}

    @api.model
    def set_default_points_money(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "points_money"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = res.points_money
            return True

        return self.env['ir.values'].create({'name': 'points_money', 'value': res.points_money, 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_conversion_points_money(self, fields):
        value = self.env['ir.values'].search([("name", "=", "conversion_points_money"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'conversion_points_money': 0.00}

        return {'conversion_points_money': float(value.value)}

    @api.model
    def set_default_conversion_points_money(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "conversion_points_money"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = float(res.conversion_points_money)
            return True

        return self.env['ir.values'].create({'name': 'conversion_points_money', 'value': float(res.conversion_points_money), 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_order_state(self, fields):
        value = self.env['ir.values'].search([("name", "=", "order_state"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'order_state': False}

        return {'order_state': value.value}

    @api.model
    def set_default_order_state(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "order_state"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = res.order_state
            return True

        return self.env['ir.values'].create({'name': 'order_state', 'value': res.order_state, 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_delay_days(self, fields):
        value = self.env['ir.values'].search([("name", "=", "delay_days"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'delay_days': 0}

        return {'delay_days': int(value.value)}

    @api.model
    def set_default_delay_days(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "delay_days"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = int(res.delay_days)
            return True

        return self.env['ir.values'].create({'name': 'delay_days', 'value': int(res.delay_days), 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_welcome_points(self, fields):
        value = self.env['ir.values'].search([("name", "=", "welcome_points"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'welcome_points': 0.00}

        return {'welcome_points': float(value.value)}

    @api.model
    def set_default_welcome_points(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "welcome_points"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = float(res.welcome_points)
            return True

        return self.env['ir.values'].create({'name': 'welcome_points', 'value': float(res.welcome_points), 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_text_welcome(self, fields):
        value = self.env['ir.values'].search([("name", "=", "text_welcome"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'text_welcome': ''}

        return {'text_welcome': value.value}

    @api.model
    def set_default_text_welcome(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "text_welcome"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = res.text_welcome
            return True

        return self.env['ir.values'].create({'name': 'text_welcome', 'value': res.text_welcome, 'model': 'customer.loyalty.settings'})

    @api.model
    def get_default_text_fe(self, fields):
        value = self.env['ir.values'].search([("name", "=", "text_fe"), ("model", "=", "customer.loyalty.settings")])
        if not value:
            return {'text_fe': ''}

        return {'text_fe': value.value}

    @api.model
    def set_default_text_fe(self, values):
        res = self.browse(values[0])
        values = self.env['ir.values'].search([("name", "=", "text_fe"), ("model", "=", "customer.loyalty.settings")])
        if values:
            values.value = res.text_fe
            return True

        return self.env['ir.values'].create({'name': 'text_fe', 'value': res.text_fe, 'model': 'customer.loyalty.settings'})
