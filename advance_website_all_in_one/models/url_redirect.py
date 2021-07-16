# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ast import literal_eval
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.http_routing.models.ir_http import slug, unslug_url

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    url_redirect = fields.Char('Redirect URL',copy=False)


    def write(self,vals):
        res = super(ProductTemplateInherit, self).write(vals)
        if 'url_redirect' in vals:
            if vals['url_redirect'] == False or vals['url_redirect'] == '':
                raise UserError(_('You can not remove SEO URL'))
        return res

class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    url_redirect = fields.Char('Redirect URL')

    def write(self,vals):
        res = super(ProductPublicCategory, self).write(vals)
        if 'url_redirect' in vals:
            if vals['url_redirect'] == False or vals['url_redirect'] == '':
                raise UserError(_('You can not remove SEO URL'))
        return res

class URLWebsiteRedirect(models.Model):
    _inherit = "website.rewrite"

    pc_id = fields.Char('Product / Category')
    url_rewrite = fields.Selection([
        ('custom_url','Custom'),
        ('product_url','Product'),
        ('category_url','Category')],string='Redirect URL',default='product_url')


class OTPConfiguration(models.Model):
    _name = 'url.config'
    _description = 'URL Configuration'

    suffix_url_in = fields.Boolean(string='Use Suffix In URL',)
    suffix_product_url = fields.Char(string='Suffix In Product URL',)
    suffix_category_url = fields.Char(string='Suffix In Category URL',)
    pattern_product_url = fields.Char(string='Pattern In Product URL',)
    pattern_category_url = fields.Char(string='Pattern In Category URL',)
    web_server_rewrite = fields.Boolean(string='Web Server Rewrite',)
    category_hierarchy = fields.Boolean(string='Category Hierarchy',)
    category_product_url = fields.Boolean(string='Category Product URL',)

    @api.model
    def default_get(self, fields):
        res = super(OTPConfiguration, self).default_get(fields)
        config_id = self.env['url.config'].sudo().search([],order="id desc", limit=1)
        if config_id:
            res.update({
                'suffix_url_in'       : config_id.suffix_url_in,
                'suffix_product_url'  : config_id.suffix_product_url,
                'suffix_category_url' : config_id.suffix_category_url,
                'pattern_product_url' : config_id.pattern_product_url,
                'pattern_category_url': config_id.pattern_category_url,
                })
            return res
        else:
            res.update({
                'suffix_url_in' : True,
                'suffix_product_url' : str('.htm'),
                'suffix_category_url': str('.net'),
                'pattern_product_url': str('name,'+'id'),
                'pattern_category_url': str('name'),
            })
            return res

    def request_url_config(self):
        for value in self:
            vals = {
                'suffix_url_in'       : value.suffix_url_in,
                'suffix_product_url'  : value.suffix_product_url,
                'suffix_category_url' : value.suffix_category_url,
                'pattern_product_url' : value.pattern_product_url,
                'pattern_category_url': value.pattern_category_url,
                }
            value.write(vals)
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: