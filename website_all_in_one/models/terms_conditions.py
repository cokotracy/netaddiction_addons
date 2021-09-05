# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo import http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.exceptions import ValidationError

class website_terms_conditions(models.Model):
    _name = 'website.terms.conditions'
    
    title  =  fields.Char('Title')
    name  =  fields.Char('Label Name')
    publish = fields.Boolean("publish terms & conditions")
    terms_conditions  =  fields.Text('Terms & Conditions')
    display_condition = fields.Selection([('model', 'Display in model popup'), ('redirect', 'Redirect to terms page'), ], 'Display Terms and Conditions', default='model')

    def sample_product_publish_button(self):
        for i in self.browse(self.ids):
            i.write({'publish': not i.publish})
        return True

    @api.constrains('publish')
    def _check_term_and_condition_unit(self):
        if self.publish == True :
            terms_ids=self.env['website.terms.conditions'].search([])
            for i in terms_ids:
                if i.id == self.id :
                    continue
                if i.publish == True:
                    raise ValidationError(_('You Can Only Publish One Terms & Conditions at a Time!!'))


class website(models.Model):
    _inherit = 'website'

    def get_website_terms_conditions(self): 
        terms_ids=self.env['website.terms.conditions'].search([('publish','=',True)])
        return terms_ids               

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    