# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, time, datetime
from openerp.exceptions import UserError,Warning
import json

class WebisteCartAdvanceSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    redirect_opt = fields.Selection([('same','Same Page'), ('cart','Cart Summary')], 'Redirect To',default='same')
    subtotal_of_orderline = fields.Boolean('Show Subtotal on orderline',default=True)
    min_cart_value = fields.Char('Minimum Website Cart Value')
    
    @api.model
    def get_values(self):
        res = super(WebisteCartAdvanceSettings, self).get_values()   

        cart_redirect = self.env["ir.config_parameter"].get_param("advance.cart.redirect")
        cart_subtotal = self.env["ir.config_parameter"].get_param("advance.cart.subtotal")
        cart_min_value = self.env["ir.config_parameter"].get_param("advance.cart.min.value")

        res.update(
            redirect_opt = cart_redirect,
            subtotal_of_orderline = cart_subtotal,
            min_cart_value = cart_min_value,
        )

        return res

    def set_values(self):
        res = super(WebisteCartAdvanceSettings, self).set_values()

        self.env['ir.config_parameter'].set_param("advance.cart.redirect", self.redirect_opt)
        self.env['ir.config_parameter'].set_param("advance.cart.subtotal", self.subtotal_of_orderline)
        self.env['ir.config_parameter'].set_param("advance.cart.min.value", self.min_cart_value)

class WebisteCartInheritWebsite(models.Model):

    _inherit = 'website'

    def get_order_line_subtotal(self):

        res_config_obj = self.env['res.config.settings']
        subtotal_of_orderline = res_config_obj.sudo().search([], limit=1, order="id desc").subtotal_of_orderline

        if subtotal_of_orderline:
            return True
        else:
            return False
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
