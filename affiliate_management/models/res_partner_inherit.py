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
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from odoo import models, fields,api,_
import random, string
import datetime
class ResPartnerInherit(models.Model):

    _inherit = 'res.partner'
    _description = "ResPartner Inherit Model"


    is_affiliate = fields.Boolean(default=False)
    res_affiliate_key = fields.Char(string="Affiliate key")
    affiliate_program_id = fields.Many2one("affiliate.program",string="Program")
    pending_amt = fields.Float(compute='_compute_pending_amt', string='Pending Amount')
    approved_amt = fields.Float(compute='_compute_approved_amt', string='Approved Amount')




    def toggle_active(self):
        for o in self:
            if o.is_affiliate:
                o.is_affiliate = False
            else:
                o.is_affiliate = True
        return super(ResPartnerInherit,self).toggle_active()

    def _compute_pending_amt(self):
        for s in self:
            visits = s.env['affiliate.visit'].search([('state','=','confirm'),('affiliate_partner_id','=',s.id)])
            amt = 0
            for v in visits:
                amt = amt + v.commission_amt
            s.pending_amt = amt

    def _compute_approved_amt(self):
        for s in self:
            visits = s.env['affiliate.visit'].search([('state','=','invoice'),('affiliate_partner_id','=',s.id)])
            amt = 0
            for v in visits:
                amt = amt + v.commission_amt
            s.approved_amt = amt

    def generate_key(self):
        ran = ''.join(random.choice('0123456789ABCDEFGHIJ0123456789KLMNOPQRSTUVWXYZ') for i in range(8))
        self.res_affiliate_key = ran


    @api.model
    def create(self,vals):
        aff_prgm = self.env['affiliate.program'].search([])[-1].id if  len(self.env['affiliate.program'].search([]))>0 else ''
        if vals.get('is_affiliate'):
            vals.update({
            'affiliate_program_id':aff_prgm
            })
        return super(ResPartnerInherit,self).create(vals)
