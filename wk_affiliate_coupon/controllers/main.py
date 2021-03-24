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
from odoo.addons.affiliate_management.controllers.main   import WebsiteSale
from odoo.addons.affiliate_management.controllers.affiliate_website import website_affiliate
from datetime import datetime, timedelta, date


class WebsiteSale(WebsiteSale):

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
        'commission_type': partner_id.affiliate_program_id.commission_type,
        }

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
                        'is_converted':True,
                        'commission_type': partner_id.affiliate_program_id.commission_type,
                        })
            # delete cookie after first sale occur
            cookie_del_status=False
            for k,v in cookies.items():
                if 'affkey_' in k:
                    cookie_del_status = result.delete_cookie(key=k)
        return result

class website_affiliate(website_affiliate):

    @http.route('/affiliate/report', type='http', auth="user", website=True)
    def report(self, **kw):
        result = super(website_affiliate,self).report(**kw)
        visits = request.env['affiliate.visit'].sudo()
        partner = request.env.user.partner_id
        ppc_visit = visits.search([('affiliate_method','=','ppc'),('affiliate_partner_id','=',partner.id),('commission_type','=','d'),'|',('state','=','invoice'),('state','=','confirm')])
        pps_visit = visits.search([('affiliate_method','=','pps'),('affiliate_partner_id','=',partner.id),('commission_type','=','d'),'|',('state','=','invoice'),('state','=','confirm')])
        result.qcontext.update({"ppc_count":len(ppc_visit),"pps_count":len(pps_visit)})
        return result

    @http.route(['/my/order','/my/order/page/<int:page>'], type='http', auth="user", website=True)
    def aff_order(self, page=1, date_begin=None, date_end=None, **kw):
        values={}
        partner = request.env.user.partner_id
        visits = request.env['affiliate.visit'].sudo()
        domain = [('commission_type','=','d'),('affiliate_partner_id','=',partner.id),('affiliate_method','=','pps'),'|',('state','=','invoice'),('state','=','confirm')]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        traffic_count = visits.search_count(domain)
        pager = request.website.pager(
            url='/my/order',
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=traffic_count,
            page=page,
            step=10
        )
        ppc_visit = visits.sudo().search(domain, limit=10, offset=pager['offset'])
        values.update({
            'pager': pager,
            'traffic': ppc_visit,
            'default_url': '/my/order',
        })
        return http.request.render('affiliate_management.affiliate_order', values)


    @http.route(['/affiliate/coupon','/affiliate/coupon/<int:id>'], type='http', auth="user", website=True)
    def coupon_details(self,**kw):
        visits = request.env['sale.coupon'].sudo()
        partner = request.env.user.partner_id
        coupon = visits.search([('is_affiliate_coupon','=',True),('partner_id','=',partner.id)])
        currency_id = request.env.user.company_id.currency_id
        values = {
        'visit_count':len(coupon),
        'coupon':coupon,
        "currency_id":currency_id,
        }
        _logger.info("======kw=====%r",kw)
        if kw.get("id"):
            coupon = visits.browse(kw.get("id"))
            _logger.info("======kw=====%r",coupon.program_id.aff_visit_id)
            values.update({"coupon":coupon,"details":True})
        return http.request.render('wk_affiliate_coupon.coupon_details', values)
