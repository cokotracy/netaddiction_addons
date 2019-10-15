# -*- coding: utf-8 -*-
import logging
import werkzeug.utils

from openerp import http
from openerp.http import request
from openerp.http import Response
from openerp.http import JsonRequest

_logger = logging.getLogger(__name__)

class ShowApp(http.Controller):

    @http.route('/show', type='http', auth='user')
    def index(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session

        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/show')

        user = request.env['res.users'].search([('id', '=', uid)])

        show_new = request.env['netaddiction.show'].search([('state', '=', 'draft')])
        show_open = request.env['netaddiction.show'].search([('state', '=', 'open')])

        return request.render(
            'netaddiction_show.index',
            {
                'user': user,
                'count_show_new': len(show_new),
                'count_show_open': len(show_open),
                'show_new': show_new,
                'show_open': show_open
            })

    @http.route('/show/<show_id>', type='http', auth='user')
    def show_pick_up(self, show_id, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        user = request.env['res.users'].search([('id', '=', uid)])

        this_show = request.env['netaddiction.show'].browse(int(show_id))
        this_show.state = 'open'

        return request.render(
            'netaddiction_show.show',
            {
                'show': this_show
            })
