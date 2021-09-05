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
from ast import literal_eval
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo import http
from odoo.http import request
from odoo import tools
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
from odoo.fields import Date
import werkzeug.utils
import werkzeug.wrappers
from odoo.addons.website_sale.controllers.main   import TableCompute
import requests
from odoo.addons.web.controllers.main import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect
from odoo.addons.affiliate_management.controllers.home import Home
from odoo.addons.website.controllers.main import Website,QueryURL
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression



class website_affiliate(Home):


    #home page of affiliate website
    @http.route('/affiliate/', auth='public',type='http', website=True)
    def affiliate(self, **kw):
        banner = request.env['affiliate.banner'].sudo().search([])
        banner_title = banner[-1].banner_title if banner else ''
        banner_image = banner[-1].banner_image if banner else ''
        ConfigValues = request.env['res.config.settings'].sudo().website_constant()
        enable_forget_pwd = ConfigValues.get('enable_forget_pwd')
        enable_login = ConfigValues.get('enable_login')
        enable_signup = ConfigValues.get('enable_signup')
        how_it_work_title = ConfigValues.get('work_title')
        how_it_work_text = ConfigValues.get('work_text')
        values = {
            'default_header':False,
            'affiliate_website':True,
            'banner_title':banner_title,
            'banner_image':banner_image,
            'enable_forget_pwd':enable_forget_pwd,
            'enable_login':enable_login,
            'enable_signup':enable_signup,
            'website_name' : request.env['website'].search([])[0].name,
            'how_it_work_title':how_it_work_title,
            'how_it_work_text'  :how_it_work_text
        }
        if request.session.get('error'):
            values.update({'error':request.session.get('error')})
        if request.session.get('success'):
            values.update({'success':request.session.get('success')})
        request.session.pop('error', None)
        request.session.pop('success', None)
        return http.request.render('affiliate_management.affiliate', values)

    @http.route('/affiliate/join', auth='public',type='json', website=True,methods=['POST'])
    def join(self,email ,**kw):
        msg = False
        aff = request.env['affiliate.request'].sudo().search([('name','=',email)])
        if aff:
            if (not aff.signup_valid) and (not aff.user_id):
                aff.regenerate_token()
                msg = "Thank you for registering with us, we have sent you the Signup mail at "+email+"."

            else:
                if aff.state == 'register' or aff.state == 'aproove':
                    msg = "Your email is already registered with us "
                else:
                    msg = "Your request is pending for approval with us, soon you will receive 'Approval' confirmation e-mail."

        else:
            aff_request = request.env['affiliate.request'].sudo().create({
            'name':email,
            'state':'draft',
            })
            msg = "Thank you for registering with us, we have sent you the Signup mail at "+email
        return msg

    @http.route('/affiliate/about',type='http', auth="user", website=True)
    def affiliate_about(self, **kw):
        partner = request.env.user.partner_id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        currency_id = request.env.user.company_id.currency_id
        ConfigValues = request.env['res.config.settings'].sudo().website_constant()
        value={
        'url': base_url+"/shop?aff_key="+partner.res_affiliate_key,
        'affiliate_key': partner.res_affiliate_key,
        'pending_amt':partner.pending_amt,
        'approved_amt':partner.approved_amt,
        'currency_id':currency_id,
        'how_it_works_title':ConfigValues.get('work_title'),
        'how_it_works_text':ConfigValues.get('work_text'),
        }
        return http.request.render('affiliate_management.about', value)

    @http.route('/affiliate/signup', auth='public',type='http', website=True)
    def register(self, **kw):
        token = request.httprequest.args.get('token')
        user = request.env['affiliate.request'].sudo().search([('signup_token','=',token)])
        term_condition = request.env['res.config.settings'].sudo().website_constant().get('term_condition')
        values = {}
        if user.signup_valid and user.state == 'draft':
            values .update({
                    'name': user.name.split('@')[0],
                    'login': user.name,
                    'token': token,
                    'term_condition':term_condition,
                })
            if request.session.get('error'):
                values.update({'error':request.session.get('error')})
        else:
            pass
        request.session.pop('error', None)
        return http.request.render('affiliate_management.register',values)


    @http.route('/affiliate/register', auth='public',type='http', website=True)
    def register_affiliate(self, **kw):
        ensure_db()
        aff_request = request.env['affiliate.request'].sudo().search([('name','=',kw.get('login'))])
        if aff_request and kw.get('confirm_password') == kw.get('password') and aff_request.signup_token == kw.get('token'):
            template_user_id = literal_eval(request.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
            template_user = request.env['res.users'].sudo().browse(template_user_id)
            auto_approve_request = request.env['res.config.settings'].sudo().website_constant().get('auto_approve_request')
            if not template_user.exists():
                raise SignupError('Invalid template user.')
            data = kw
            redirect_url = "/"
            values = { key: data.get(key) for key in ('login', 'name') }
            values['email'] = data.get('email') or values.get('login')
            values['lang'] = request.lang.code
            values['active'] = True
            no_invitation_mail = True
            values['password'] = data.get('password',"")
            try:
                with request.env.cr.savepoint():
                    user = template_user.with_context(no_reset_password = no_invitation_mail).copy(values)
                    _logger.info('------user.partner--%r-----',user.partner_id)
                    # update phoen no. and comment in res.partner
                    user.partner_id.comment = kw.get('comment')
                    user.partner_id.phone = kw.get('phone')
                    # update affiliate.request with partner and user id and state
                    aff_request.partner_id = user.partner_id.id
                    aff_request.user_id = user.id
                    aff_request.state = 'register'
                request.env.cr.commit()
                # check the config for auto approve the request
                if auto_approve_request:
                    aff_request.action_aproove()
                db = request.env.cr.dbname
                return login_and_redirect(db, data['login'], data['password'],redirect_url='/affiliate')
            except Exception as e:
                _logger.error("Error123: %r"%e)
            return http.redirect_with_hash('/')
        else:
            if kw.get('password')!= kw.get('confirm_password'):
                request.session['error']= "Passwords Does't match."
                return request.redirect('/affiliate/signup?token='+kw.get('token'), 303)
            else:
                request.session['error']= "something went wrong.."
                return request.redirect('/affiliate/', 303)

    @http.route('/affiliate/register/confirmation', auth='public',type='http', website=True)
    def register_affiliate_confirmation(self, **kw):
        return http.request.render('affiliate_management.confirmation', {
        })


    @http.route('/affiliate/home',type='http', auth="user", website=True)
    def home(self, **kw):
        return http.request.render('affiliate_management.report', {
        })


    @http.route('/affiliate/report', type='http', auth="user", website=True)
    def report(self, **kw):
        partner = request.env.user.partner_id
        enable_ppc = request.env['res.config.settings'].sudo().website_constant().get('enable_ppc')
        currency_id = request.env.user.company_id.currency_id
        visits = request.env['affiliate.visit'].sudo()
        ppc_visit = visits.search([('affiliate_method','=','ppc'),('affiliate_partner_id','=',partner.id),'|',('state','=','invoice'),('state','=','confirm')])
        pps_visit = visits.search([('affiliate_method','=','pps'),('affiliate_partner_id','=',partner.id),'|',('state','=','invoice'),('state','=','confirm')])
        values = {
        'pending_amt':partner.pending_amt,
        'approved_amt':partner.approved_amt,
        'ppc_count':len(ppc_visit),
        'pps_count':len(pps_visit),
        'enable_ppc':enable_ppc,
        "currency_id":currency_id,
        }
        return http.request.render('affiliate_management.report', values)

    @http.route(['/my/traffic','/my/traffic/page/<int:page>'], type='http', auth="user", website=True)
    def traffic(self, page=1, date_begin=None, date_end=None, **kw):
        values={}
        partner = request.env.user.partner_id
        visits = request.env['affiliate.visit'].sudo()
        domain = [('affiliate_partner_id','=',partner.id),('affiliate_method','=','ppc'),'|',('state','=','invoice'),('state','=','confirm')]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        traffic_count = visits.search_count(domain)
        pager = request.website.pager(
            url='/my/traffic',
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=traffic_count,
            page=page,
            step=10
        )
        ppc_visit = visits.search(domain, limit=10, offset=pager['offset'])
        values.update({
            'pager': pager,
            'traffic': ppc_visit,
            'default_url': '/my/traffic'
        })

        return http.request.render('affiliate_management.affiliate_traffic', values)


    @http.route(['/my/traffic/<int:traffic>'], type='http', auth="user", website=True)
    def aff_traffic_form(self, traffic=None, **kw):
        traffic_visit = request.env['affiliate.visit'].sudo().browse([traffic])
        return request.render("affiliate_management.traffic_form", {
            'traffic_detail': traffic_visit,
            'product_detail':request.env['product.product'].browse([traffic_visit.type_id]),
        })



    @http.route(['/my/order','/my/order/page/<int:page>'], type='http', auth="user", website=True)
    def aff_order(self, page=1, date_begin=None, date_end=None, **kw):
        values={}
        partner = request.env.user.partner_id
        visits = request.env['affiliate.visit'].sudo()
        domain = [('affiliate_partner_id','=',partner.id),('affiliate_method','=','pps'),'|',('state','=','invoice'),('state','=','confirm')]
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


    @http.route(['/my/order/<int:order>'], type='http', auth="user", website=True)
    def aff_order_form(self, order=None, **kw):
        order_visit = request.env['affiliate.visit'].sudo().browse([order])
        return request.render("affiliate_management.order_form", {
            'order_visit_detail': order_visit,
            'product_detail' :order_visit.sales_order_line_id.sudo()
        })


    # Routes for the payment template
    @http.route(['/affiliate/payment','/affiliate/payment/page/<int:page>'], type='http', auth="user", website=True)
    def payment(self, page=1, date_begin=None, date_end=None, **kw):
        values={}
        partner = request.env.user.partner_id
        invoices = request.env['account.move']
        domain = [('partner_id','=',partner.id),('payment_state','=','paid'),('ref','=',None)]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        invoice_count = invoices.search_count(domain)

        pager = request.website.pager(
            url='/affiliate/payment',
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=invoice_count,
            page=page,
            step=10
        )
        invoice_list = invoices.search(domain, limit=10, offset=pager['offset'])

        values.update({
            'pager': pager,
            'invoices': invoice_list,
            'default_url': '/affiliate/payment',
        })
        return http.request.render('affiliate_management.payment_tree',values )


    @http.route(['/my/invoice/<int:invoice>'], type='http', auth="user", website=True)
    def aff_invoice_form(self, invoice=None, **kw):
        inv = request.env['account.move'].sudo().browse([invoice])
        return request.render("affiliate_management.payment_form", {
            'invoice': inv,

        })

    @http.route('/affiliate/tool', auth='user',type='http', website=True)
    def tool(self, **kw):
        """actions for Tool "affiliate/tool"""
        return http.request.render('affiliate_management.tool',{})


    @http.route('/tool/create_link', auth='user',type='http', website=True)
    def create_link(self, **kw):
        """generate affiliate link by url"""
        partner = request.env.user.partner_id
        link = kw.get("link")
        result = self.check_link_validation(link)
        if kw.get('link') and partner.res_affiliate_key and result:
          request.session['generate_link'] = link+'?aff_key='+partner.res_affiliate_key
        return request.redirect('/tool/link_generator/', 303)

    @http.route("/tool/link_generator", auth='user',type='http', website=True)
    def link_generator(self, **kw):
        partner = request.env.user.partner_id
        values={}
        if request.session.get('generate_link'):
            values.update({
                'generate_link':request.session.get('generate_link'),
                'error':request.session.get('error')
                })
        if request.session.get('error'):
            values.update({
                'error':request.session.get('error')
                })
        request.session.pop('generate_link', None)
        request.session.pop('error', None)
        return http.request.render('affiliate_management.link_generator',values)

    def check_link_validation(self,link):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        try:
            r = requests.get(link,verify=False)

            if r.status_code == 200:
                langs = [l.code for l in request.website.language_ids]

                link_arr = link.split("/")
                # if a language is already in the path, remove it
                if link_arr[1] in langs:
                    link_arr.pop(1)
                link_base_url = link_arr[0]+"//"+link_arr[2]

                if base_url == link_base_url :
                    if 'shop' in link_arr and 'product' in link_arr:
                        return True
                    else:
                        request.session['error'] = "Url doesn't have shop/product"
                        return False
                else:
                    request.session['error'] = "Base Url doesn't match"
                    return False
            else:
                request.session['error'] = "Please enter a Valid Url. Bad response from "+link
                return False
        except Exception as e:
            request.session['error'] = "Please enter a Valid Url. + %r"%e
            return False




    @http.route("/tool/product_link", auth='user',type='http', website=True)
    def product_link(self, **kw):
        values={}
        category = request.env['product.public.category'].sudo().search([])
        values.update({
            'category': category,
            })
        return http.request.render('affiliate_management.product_link',values)


    # search the product on criteria category and published product
    @http.route("/search/product", auth='user',type='http', website=True)
    def search_product(self, **kw):
        domain = request.website.sale_product_domain()
        if kw.get('name'):

            domain += [
                ('website_published','=',True),'|', '|', '|', ('name', 'ilike', kw.get('name')), ('description', 'ilike', kw.get('name')),
                ('description_sale', 'ilike', kw.get('name')), ('product_variant_ids.default_code', 'ilike', kw.get('name'))]

        if kw.get('categories'):
            category_id = request.env['product.public.category'].sudo().search([('name','=',kw.get('categories'))],limit=1)
            if  category_id:
                domain += [('public_categ_ids', 'child_of', int(category_id.id))]

        partner = request.env.user.partner_id
        values={}
        category = request.env['product.public.category'].sudo().search([])
        values.update({
            'category': category,
            })
        product_template = request.env['product.template'].sudo()
        products = product_template.search(domain)
        if products:
            values.update({
                'bins': TableCompute().process(products, 10),
                'search_products':products,
                'rows':4,
                'partner_key': partner.res_affiliate_key,
                'base_url': request.env['ir.config_parameter'].sudo().get_param('web.base.url')

                })
        _logger.info("=======values====%r",values)
        return http.request.render('affiliate_management.product_link',values)


    @http.route('/tool/generate_banner', auth='user',type='http', website=True)
    def tool_banner(self, **kw):
        partner = request.env.user.partner_id
        banner_image_ids = request.env['affiliate.image'].sudo().search([('image_active','=',True)])
        product = request.env['product.template'].sudo().search([('id','=',kw.get('product_id'))])
        values={
        'banner_button':banner_image_ids,
        'product':product,
        }
        return http.request.render('affiliate_management.generate_banner',values)


    @http.route("/tool/generate_button_link", auth='user',type='http', website=True)
    def generate_button_link(self, **kw):
        partner = request.env.user.partner_id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        values ={
            'partner_key': partner.res_affiliate_key,
            'product_id':kw.get('product_id'),
            'base_url' : base_url
        }
        selected_image= kw.get('choose_banner').split("_")
        if selected_image[0] == 'button':
            _logger.info("-----selected button image id ---%r---",selected_image[1])
            button = request.env['affiliate.image'].sudo().browse([int(selected_image[1])])
            values.update({
                "button":button
                })
        else:
            if selected_image[0] == 'product':
                values.update({
                "is_product":True
                })
                _logger.info("-----selected product image id ---%r---",selected_image[1])
        return http.request.render('affiliate_management.generate_button_link',values)



    @http.route("/affiliate/request", type='json', auth="public", methods=['POST'], website=True)
    def portal_user(self, user_id,**kw):
        User = request.env['res.users'].sudo().browse([request.uid])
        AffRqstObj = request.env['affiliate.request'].sudo()
        vals ={
        'name':User.partner_id.email,
        'partner_id': User.partner_id.id,
        'user_id': request.uid,
        'state':'register',
        }
        aff_request = AffRqstObj.create(vals)
        auto_approve_request = request.env['res.config.settings'].sudo().website_constant().get('auto_approve_request')
        if auto_approve_request:
            aff_request.action_aproove()
        return aff_request and True or False
