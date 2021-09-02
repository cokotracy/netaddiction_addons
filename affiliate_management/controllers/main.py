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
from odoo import http
from odoo.http import request
from odoo import fields
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.website_sale.controllers.main   import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
import datetime


class WebsiteSale(WebsiteSale):

    def create_aff_visit_entry(self,vals):
      ppc_exist = self.check_ppc_exist(vals)
      if ppc_exist:
        visit = ppc_exist
      else:
        visit = request.env['affiliate.visit'].sudo().create(vals)
      return visit


    def check_ppc_exist(self,vals):
      domain = [('type_id','=',vals['type_id']),('affiliate_method','=',vals['affiliate_method']),('affiliate_key','=',vals['affiliate_key']),('ip_address','=',vals['ip_address'])]
      visit = request.env['affiliate.visit'].sudo().search(domain)
      check_unique_ppc = request.env['res.config.settings'].sudo().website_constant().get('unique_ppc_traffic')
      # "check_unique_ppc" it cheacks that in config setting wheather the unique ppc is enable or not
      if check_unique_ppc:
        if visit:
          return visit
        else:
          return False
      else:
          return False

# override shop action in website_sale
    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True,sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        enable_ppc = request.env['res.config.settings'].sudo().website_constant().get('enable_ppc')
        expire = False
        result = super(WebsiteSale,self).shop(page=page, category=category, search=search, ppg=ppg, **post)
        aff_key = request.httprequest.args.get('aff_key')
        if category and aff_key:
            expire = self.calc_cookie_expire_date()
            path = request.httprequest.full_path
            partner_id = request.env['res.partner'].sudo().search([('res_affiliate_key','=',aff_key),('is_affiliate','=',True)])
            vals = self.create_affiliate_visit(aff_key,partner_id,category)
            vals.update({'affiliate_type':'category'})
            if ( len(partner_id) == 1):
                affiliate_visit = self.create_aff_visit_entry(vals) if enable_ppc else False
                result.set_cookie(key='affkey_%s'%(aff_key), value='category_%s'%(category.id),expires=expire)
            else:
                _logger.info("=====affiliate_visit not created by category===========")
        else:
            if aff_key:
                expire = self.calc_cookie_expire_date()
                partner_id = request.env['res.partner'].sudo().search([('res_affiliate_key','=',aff_key),('is_affiliate','=',True)])
                if partner_id:
                    result.set_cookie(key='affkey_%s'%(aff_key), value='shop',expires=expire)
        return result


    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def old_product(self, product, category='', search='', **kwargs):
      _logger.info("=====product page=========")
      _logger.info("=====product page aff_key==%r=========",request.httprequest.args)
      enable_ppc = request.env['res.config.settings'].sudo().website_constant().get('enable_ppc')
      expire = self.calc_cookie_expire_date()

      result = super(WebsiteSale,self).old_product(product=product, category=category, search=search, **kwargs)
      if request.httprequest.args.get('aff_key'):
        # path is the complete url with url = xxxx?aff_key=XXXXXXXX
        path = request.httprequest.full_path
        # aff_key is fetch from url
        aff_key = request.httprequest.args.get('aff_key')
        partner_id = request.env['res.partner'].sudo().search([('res_affiliate_key','=',aff_key),('is_affiliate','=',True)])
        vals = self.create_affiliate_visit(aff_key,partner_id,product)
        vals.update({'affiliate_type':'product'})
        if ( len(partner_id) == 1  and 'product' in path):
          affiliate_visit = self.create_aff_visit_entry(vals) if enable_ppc else False
          # "create_aff_visit_entry " this methods check weather the visit is already created or not or if created return the no. of existing record in object
          result.set_cookie(key='affkey_%s'%(aff_key),value='product_%s'%(product.id),expires=expire)
          _logger.info("============affiliate_visit created by product==%r=======",affiliate_visit)
        else:
          _logger.info("=====affiliate_visit not created by product===========%s %s"%(aff_key,partner_id))
      return result



    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
      _logger.info('-----------payment---------------')
      result = super(WebsiteSale,self).payment_confirmation(**post)
      # here result id http.render argument is http.render{ http.render(template, qcontext=None, lazy=True, **kw) }
      sale_order_id = result.qcontext.get('order')
      return self.update_affiliate_visit_cookies( sale_order_id,result )


    def create_affiliate_visit(self,aff_key,partner_id,type_id):
      """ method to  delete the cookie after update function on id"""
      vals = {
            'affiliate_method':'ppc',
            'affiliate_key':aff_key,
            'affiliate_partner_id':partner_id.id,
            'url':request.httprequest.full_path,
            'ip_address':request.httprequest.environ['REMOTE_ADDR'],
            'type_id':type_id.id,
            'convert_date':fields.datetime.now(),
            'affiliate_program_id': partner_id.affiliate_program_id.id,
        }
      return vals

    def update_affiliate_visit_cookies(self , sale_order_id ,result):
      """update affiliate.visit from cokkies data i.e created in product and shop method"""
      cookies = dict(request.httprequest.cookies)
      visit = request.env['affiliate.visit']
      arr=[]# contains cookies product_id
      for k,v in cookies.items():
        if 'affkey_' in k:
          arr.append(k.split('_')[1])
      if arr:
          partner_id = request.env['res.partner'].sudo().search([('res_affiliate_key','=',arr[0]),('is_affiliate','=',True)])
          for s in sale_order_id.order_line:
            if len(arr)>0 and partner_id:
              product_tmpl_id = s.product_id.product_tmpl_id.id
              aff_visit = visit.sudo().create({
                'affiliate_method':'pps',
                'affiliate_key':arr[0],
                'affiliate_partner_id':partner_id.id,
                'url':"",
                'ip_address':request.httprequest.environ['REMOTE_ADDR'],
                'type_id':product_tmpl_id,
                'affiliate_type': 'product',
                'type_name':s.product_id.id,
                'sales_order_line_id':s.id,
                'convert_date':fields.datetime.now(),
                'affiliate_program_id': partner_id.affiliate_program_id.id,
                'product_quantity' : s.product_uom_qty,
                'is_converted':True
              })
          # delete cookie after first sale occur
          cookie_del_status=False
          for k,v in cookies.items():
            if 'affkey_' in k:
              cookie_del_status = result.delete_cookie(key=k)
      return result


    def calc_cookie_expire_date(self):
      ConfigValues = request.env['res.config.settings'].sudo().website_constant()
      cookie_expire = ConfigValues.get('cookie_expire')
      cookie_expire_period = ConfigValues.get('cookie_expire_period')
      time_dict = {
      'hours':cookie_expire,
      'days':cookie_expire*24,
      'months':cookie_expire*24*30,
      }
      return datetime.datetime.utcnow() + datetime.timedelta(hours=time_dict[cookie_expire_period])
