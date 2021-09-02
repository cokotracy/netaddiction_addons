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
from odoo.http import request


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.move'


    aff_visit_id = fields.One2many('affiliate.visit','act_invoice_id',string="Report")


#     def write(self, vals):
#         result = super(AccountInvoiceInherit,self).write(vals)
#         if self.ref:
#             move_id = self.env["account.move"].sudo().search([("name","=",self.ref)])
#             if self.payment_state == "paid":

#                 if move_id.aff_visit_id:
#                     move_id.aff_visit_id.write({"state":"paid"})

#         return result




class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'
    _description = "Account Payment Inherit Model"


    # def action_validate_invoice_payment(self):
    def post(self):
        result = super(AccountPaymentInherit,self).post()
        if result and self.invoice_ids:
            move_id = self.invoice_ids[0]
            if move_id.payment_state == "paid" and move_id.aff_visit_id and move_id.aff_visit_id.state != "paid":
                move_id.aff_visit_id.write({"state":"paid"})

        return result
