# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _

class ProductAttachment(models.Model):

    _name = 'product.attachment'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    attachment = fields.Binary(string='Attachment')
    file_name = fields.Char()
    product_tmpl_id = fields.Many2one('product.template','Product')

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    attachments = fields.One2many('product.attachment','product_tmpl_id','Images')
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
