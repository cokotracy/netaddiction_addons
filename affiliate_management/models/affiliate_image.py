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
class AffiliateImage(models.Model):
    _name = "affiliate.image"
    _description = "Affiliate Image Model"


    name = fields.Char(string = "Name",required=True)
    title = fields.Char(string = "Title",required=True)
    banner_height = fields.Integer(string = "Height")
    bannner_width =  fields.Integer(string = "Width")
    image = fields.Binary(string="Image",required=True)
    user_id = fields.Many2one('res.users', string='current user', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    image_active = fields.Boolean(string="Active",default=True)


    def toggle_active_button(self):
        if self.image_active:
            self.image_active = False
        else:
            self.image_active = True


    @api.model
    def create(self,vals):
        if vals.get('image') == False:
            raise UserError("Image field is mandatory")
        return super(AffiliateImage,self).create(vals)