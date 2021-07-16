# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo import SUPERUSER_ID

class product_template(models.Model):
    _inherit = 'product.template'
    
    select_label = fields.Many2one('website.product.label', 'Select Product Label')
    label_image = fields.Binary('Label Image')

    @api.onchange('select_label')
    def onchange_product_label(self):
        self.label_image = self.select_label.image        
            
            
class website_product_label(models.Model):
    _name='website.product.label'

    name  =  fields.Char('Label Name')
    image = fields.Binary('Image')
    height = fields.Char('Height(in px)')
    width = fields.Char('Width(in px)')
    position = fields.Selection([
        ('topleft', 'Top Left'),
        ('topright', 'Top Right'),
        ('topcenter', 'Top Center'),
        ('center', 'Center'),
        ('bottomleft', 'Bottom Left'),
        ('bottomright', 'Bottom Right'),
        ('bottomcenter', 'Bottom Center'),
        ], 'Position of Label', default="topleft",  select=True)
    margin_top = fields.Char('Margin Top(in px)')
    margin_bottom = fields.Char('Margin Bottom(in px)')
    margin_left = fields.Char('Margin Left(in px)')
    margin_right = fields.Char('Margin Right(in px)')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
