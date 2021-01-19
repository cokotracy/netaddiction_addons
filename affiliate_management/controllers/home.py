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
import werkzeug.utils
import werkzeug.wrappers

from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)
from odoo.addons.web.controllers.main import Home

import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_resource_path
from odoo.tools import topological_sort
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlwt

from odoo.http import content_disposition, dispatch_rpc, request
                      # serialize_exception as _serialize_exception
from odoo.exceptions import AccessError
from odoo.models import check_method_name


class Home(Home):

    @http.route(website=True, auth="public")
    def web_login(self, redirect=None, *args, **kw):
        # _logger.info("------inside weblgin ----%r----",kw)
        response = super(Home, self).web_login(redirect=redirect, *args, **kw)
        # kw.get('affiliate_login_form') is hidden field in login form of affiliate home page
        check_affiliate = request.env['res.users'].sudo().search([('login','=',kw.get('login'))]).partner_id.is_affiliate
        if kw.get('affiliate_login_form') and response.qcontext.get('error'):
            request.session['error']= 'Wrong login/password'
            return request.redirect('/affiliate/',303)
        else:
            if kw.get('affiliate_login_form') and check_affiliate:
                return super(Home, self).web_login(redirect='/affiliate/about', *args, **kw)
            else:
                return response

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        partner = request.env['res.users'].sudo().browse([request.session.uid])
        if partner.partner_id.is_affiliate:
            request.session.logout(keep_db=True)
            return werkzeug.utils.redirect('/affiliate', 303)
        else:
            request.session.logout(keep_db=True)
            return werkzeug.utils.redirect(redirect, 303)
