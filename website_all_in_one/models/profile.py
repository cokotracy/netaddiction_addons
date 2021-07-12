# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class Website(models.Model):
    _inherit = 'website'

    def get_country_list(self):            
        country_ids=self.env['res.country'].search([])
        return country_ids
        
    def get_state_list(self):            
        state_ids=self.env['res.country.state'].search([])
        return state_ids
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

