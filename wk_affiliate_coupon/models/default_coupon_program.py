#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import api, fields, models, _
from odoo.http import request
from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)


class CouponsProgram(models.Model):
    _name = 'coupons.program'

    coupon_name = fields.Char(string='Name', size=100 , help="default name of the coupon")
    coupon_validity = fields.Integer(string='Validity(in days)', help="Validity of this Coupon in days")
    pps_discount_type = fields.Selection([('fixed_amount', 'Fixed Amount'),('percentage', 'Percentage')], string="PPS Discount Type",default="fixed_amount")
    pps_fixed_amount = fields.Float(string='Amount',default=0.0)
    pps_percentage = fields.Float(string='Percent',required=True,default=0.0)
    ppc_discount_type = fields.Selection([('fixed_amount', 'Fixed Amount'),('percentage', 'Percentage')], string="PPS Discount Type",default="fixed_amount")
    ppc_fixed_amount = fields.Float(string='Amount',default=0.0)
    ppc_percentage = fields.Float(string='Percent',required=True,default=0.0)


class SaleCoupon(models.Model):
    _inherit = 'coupon.coupon'

    is_affiliate_coupon = fields.Boolean(string='Affiliate Coupon',default=False)

class SaleCouponProgram(models.Model):
    _inherit = 'coupon.program'

    aff_visit_id = fields.One2many('affiliate.visit','sale_coupon_program_id',string="Visit Related To Coupon")
    coupon_type = fields.Selection([('single', 'Single'),('consolidate', 'Consolidate')],readonly='True', string="Coupon Type")
