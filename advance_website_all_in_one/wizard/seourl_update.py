# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import math
import psycopg2
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TemplateSEOURL(models.TransientModel):
    _name="template.seourl"
    _description = 'Template SEOURL'
    
    name = fields.Integer('Product Count',default=0)

    @api.model
    def default_get(self, fields):
        res = super(TemplateSEOURL, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        products = self.env[active_model].browse(active_ids)
        actual_product = self.env['product.template'].search([('website_published', '=', True)])
        url_id = self.env['url.config'].sudo().search([],order="id desc", limit=1)
        if url_id:
            if len(actual_product) != len(products):
                if any(product.url_redirect == '' or product.url_redirect == False for product in actual_product):
                    raise UserError(_('Set SEO URL for All Published Products!!!! \n You can not set it partial !!'))
            else:
                res.update({
                    'name' : len(products)
                    })
                return res
        else:
            raise UserError(_('Please Configure URL Configurations!!!!'))


    def return_ok(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        products = self.env[active_model].sudo().browse(active_ids)
        model_id = self.env['ir.model'].sudo().search([('model','=',str(active_model))])
        url_id = self.env['url.config'].sudo().search([],order="id desc", limit=1)
        website_id = self.env['url.config'].sudo().search([],order="id asc", limit=1)
        redirect_obj = self.env['website.rewrite']
        if url_id:
            for product in products:
                url_build = url_id.pattern_product_url
                url_list = url_build.split(",")
                product_url = []
                for field in url_list:
                    for field_name in model_id.field_id:
                        if field_name.name == field:
                            sql= "SELECT %s FROM product_template WHERE id=%s" % (field,product.id)
                            try:
                                self.env.cr.execute(sql)
                            except psycopg2.ProgrammingError as e:
                                raise UserError(_('Invalid Field in URL Configurations!!!! %s' % field))

                            [value] = self.env.cr.fetchall()           
                            if value[0] != None:
                                product_url.append(value[0])


                seourl = ''
                for url in product_url:
                    u = ''
                    if type(url) == int:
                        u = str(url)
                    else:
                        if isinstance(url, float):
                            u = str(url).lower()
                        elif isinstance(url, bool):
                            u = str(url)
                        else:
                            u = url.replace('  ',' ')
                            u = u.replace(' ','-').lower()
                            u = u.replace('_','-')
                            u = u.replace('/','')
                    seourl += str(u.lower() + '-')
                seourl = seourl.replace('--','-')
                seourl = seourl[:-1]
                product.write({'url_redirect' : seourl})
                redirect_ids = redirect_obj.sudo().search([('pc_id','=',product.id),('url_rewrite','=','product_url')])
                if not redirect_ids:
                    url_from = ''
                    if product.default_code:
                        url_from = "/%s-%s-%s" % (str(product.default_code.replace('_','-')),str(product.name.replace(' ','-')),str(product.id))
                    else:
                        url_from = "/%s-%s" % (str(product.name.replace(' ','-')),str(product.id))
                    url_to = "/%s" % str(product.name).replace(' ','-').lower()
                    vals = {
                    'name' : seourl,
                    'redirect_type' : '301',
                    'url_from' : url_from,
                    'url_to' : url_to,
                    'pc_id' : product.id,
                    'url_rewrite' : 'product_url',
                    'active' : True,
                    'website_id' : website_id.id,
                    }
                    redirect_obj.sudo().create(vals)
        else:
            raise UserError(_('Please Configure URL Configurations!!!!'))

class CategorySEOURL(models.TransientModel):
    _name="public.category.seourl"
    _description = 'Category SEOURL'

    name = fields.Integer('Product Count',default=0)

    @api.model
    def default_get(self, fields):
        res = super(CategorySEOURL, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        cateogries = self.env[active_model].sudo().browse(active_ids)
        actual_category = self.env['product.public.category'].search([])
        url_id = self.env['url.config'].sudo().search([],order="id desc", limit=1)
        if url_id:
            if len(actual_category) != len(cateogries):
                if any(category.url_redirect == '' or category.url_redirect == False for category in actual_category):
                    raise UserError(_('Set SEO URL for All Cateogries!!!! \n You can not set it partial !!'))
            else:
                res.update({
                    'name' : len(cateogries)
                })
                return res
        else:
            raise UserError(_('Please Configure URL Configurations!!!!'))

    def return_ok(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        cateogries = self.env[active_model].browse(active_ids)
        model_id = self.env['ir.model'].sudo().search([('model','=',str(active_model))])
        url_id = self.env['url.config'].sudo().search([],order="id desc", limit=1)
        website_id = self.env['url.config'].sudo().search([],order="id asc", limit=1)
        redirect_obj = self.env['website.rewrite']
        if url_id:
            for category in cateogries:
                url_build = url_id.pattern_category_url
                url_list = url_build.split(",")
                category_url = []
                
                for field in url_list:
                    for field_name in model_id.field_id:
                        if field_name.name == field:
                            
                            sql= "SELECT %s FROM product_public_category WHERE id=%s" % (field,category.id)
                            try:
                                self.env.cr.execute(sql)
                            except psycopg2.ProgrammingError as e:
                                raise UserError(_('Invalid Field in URL Configurations!!!! %s' % field))
                            [value] = self.env.cr.fetchall()           
                            
                            if value[0] != None:
                                category_url.append(value[0])
                
                seourl = ''
                for url in category_url:
                    u = ''
                    if type(url) == int:
                        u = str(url)
                    else:
                        u = url.replace('  ',' ')
                        u = u.replace(' ','-').lower()
                        u = u.replace('_','-')
                        u = u.replace('/','')
                    
                    seourl += str(u + '-')
                seourl = seourl.replace('--','-')
                seourl = seourl[:-1]
                category.sudo().write({'url_redirect' : seourl})

                redirect_ids = redirect_obj.sudo().search([('pc_id','=',category.id),('url_rewrite','=','product_url')])
                if not redirect_ids:
                    url_from = "/%s-%s" % (str(category.name),str(category.id))
                    url_to = "/%s" % str(category.name).lower()
                    vals = {
                    'name' : seourl,
                    'redirect_type' : '301',
                    'url_from' : url_from,
                    'url_to' : url_to,
                    'pc_id' : category.id,
                    'url_rewrite' : 'category_url',
                    'active' : True,
                    'website_id' : website_id.id,
                    }
                    redirect_obj.sudo().create(vals)
        else:
            raise UserError(_('Please Configure URL Configurations!!!!'))