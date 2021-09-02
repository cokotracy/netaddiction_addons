# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields,SUPERUSER_ID, tools, _
from odoo.exceptions import UserError, ValidationError

class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = "res.partner"
    _description = 'Res Partner'
    
    product_ids = fields.Many2many('product.template', 'product_template_id','res_partner_id','product_partner_res',string='Products')
    product_categ_ids = fields.Many2many('product.category','categ_id','res_partner_categ_id','product_category',string="Product Category")
    hide_product_ids = fields.Many2many('product.template', string='Products')
    hide_product_categ_ids = fields.Many2many('product.category', string="Product Category") 


class visitor_product(models.TransientModel):
    _inherit = 'res.config.settings'

    visitor_product_ids = fields.Many2many('product.template', 'prod_tem_id','visitor_partner_id','product_visitor_res',string='Products')
    visitor_product_categ_ids = fields.Many2many('product.category','visitor_categ_id','res_part_categ_id','visitor_product_category',string="Product Category")
    visitor_hide_product_ids = fields.Many2many('product.template',string='Products')
    visitor_hide_product_categ_ids = fields.Many2many('product.category',string="Product Category")

    @api.model
    def default_get(self,fields):
        res = super(visitor_product, self).default_get(fields)
        visitor_id = self.sudo().search([], limit=1, order="id desc")
        
        product_list = []
        pro_categ_list = []
        hide_product_list = []
        hide_pro_categ_list = []

        if visitor_id:
            for visitor_products in visitor_id.visitor_product_ids:
                product_list.append(visitor_products.id)
            res.update(
                {
                    'visitor_product_ids':[(6,0,product_list)],
                }
            )

            for visitor_hide_products in visitor_id.visitor_hide_product_ids:
                hide_product_list.append(visitor_hide_products.id)
            res.update(
                {
                    'visitor_hide_product_ids':[(6,0,hide_product_list)],
                }
            )
            
            for visitor_product_categ in visitor_id.visitor_product_categ_ids:
                pro_categ_list.append(visitor_product_categ.id)
            res.update(
                {
                    'visitor_product_categ_ids':[(6,0,pro_categ_list)],
                }
            )

            for visitor_hide_product_categ in visitor_id.visitor_hide_product_categ_ids:
                hide_pro_categ_list.append(visitor_hide_product_categ.id)
            res.update(
                {
                    'visitor_hide_product_categ_ids':[(6,0,hide_pro_categ_list)],
                }
            )

            show_product_list = [elem for elem in product_list if elem not in hide_product_list]
            show_pro_categ_list = [elem for elem in pro_categ_list if elem not in hide_pro_categ_list]
            res.update(
                {
                    'visitor_product_ids':[(6,0,show_product_list)],
                }
            )
            res.update(
                {
                    'visitor_product_categ_ids':[(6,0,show_pro_categ_list)],
                }
            )
            res_obj = self.env['res.partner'].sudo().search([('name','=','Public user'),('active','=',False)])
            res_obj.update(
                {
                    'product_ids':[(6,0,show_product_list)],
                    'product_categ_ids' : [(6,0,show_pro_categ_list)],
                    'hide_product_ids':[(6,0,hide_product_list)],
                    'hide_product_categ_ids' : [(6,0,hide_pro_categ_list)],
                }
            )
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

