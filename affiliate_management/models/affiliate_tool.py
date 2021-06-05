# -*- coding: utf-8 -*-
#################################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
#################################################################################
from odoo import models,fields,api,_
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class AffiliateTool(models.TransientModel):
    _name = 'affiliate.tool'
    _description = "Affiliate Tool Model"

    @api.depends('entity','aff_product_id','aff_category_id')
    def _make_link(self):
            key = ""
            if self.env['res.users'].browse(self.env.uid).res_affiliate_key:
                key = self.env['res.users'].browse(self.env.uid).res_affiliate_key
            type_url = ""
            if self.entity == 'product':
                type_url = '/shop/product/'+str(self.aff_product_id.id)
            if self.entity == 'category':
                type_url = '/shop/category/'+str(self.aff_category_id.id)
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            if self.entity and (self.aff_product_id or self.aff_category_id):
                self.link = base_url+type_url+"?aff_key="+key
            else:
                self.link = ""

    @api.onchange('entity')
    def _blank_field(self):
        self.aff_product_id = ""
        self.aff_category_id = ""
        self.link = ""
    name = fields.Char(string="Name")
    entity = fields.Selection([('product','Product'),('category','Category')],string="Choose Entity",required=True)
    aff_product_id = fields.Many2one('product.template', string='Product')
    aff_category_id = fields.Many2one('product.public.category',string='Category')
    link = fields.Char(string='Link',compute='_make_link')
    user_id = fields.Many2one('res.users', string='current user', index=True, track_visibility='onchange', default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('affiliate.tool')
        new_url =  super(AffiliateTool,self).create(vals)
        return new_url