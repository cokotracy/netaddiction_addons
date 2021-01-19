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

class AffiliateProductPricelistItem(models.Model):
    _name = "affiliate.product.pricelist.item"
    _description = "Affiliate Product Pricelist Item Model"
    _order = 'sequence'

    name = fields.Char(string="Name")
    advance_commision_id = fields.Many2one('advance.commision')
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product')], "Apply On",
        default='3_global', required=True,
        help='Pricelist Item applicable on selected option')
    categ_id = fields.Many2one(
        'product.public.category', 'Product Category', ondelete='cascade',
        help="Specify a product category if this rule only applies to products belonging to this eccmmerce website category or its children categories. Keep empty otherwise.")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', ondelete='cascade',
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    compute_price = fields.Selection([
        ('fixed', 'Fix Price'),
        ('percentage', 'Percentage (discount)')], index=True, default='fixed')
    fixed_price = fields.Float('Fixed Price')
    percent_price = fields.Float('Percentage Price')

    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,readonly='True')
    sequence = fields.Integer(required=True, default=1,
        help="The sequence field is used to define order in which the pricelist item are applied.")

    # @api.multi
    def write(self, vals):
        if 'fixed_price' in vals.keys() or 'compute_price' in vals.keys() or 'percent_price' in vals.keys():
            compute_price = vals.get('compute_price') if 'compute_price' in vals.keys() else self[-1].compute_price
            change_value = None
            if compute_price == 'fixed':
                if 'fixed_price' in vals.keys():
                    change_value = vals.get('fixed_price')
                else:
                    change_value = self[-1].fixed_price
            else:
                if 'percent_price' in vals.keys():
                    change_value = vals.get('percent_price')
                else:
                    change_value = self[-1].percent_price

            if change_value <= 0:
                raise UserError("Price List Item value must be greater than zero.")

        return super(AffiliateProductPricelistItem,self).write(vals)

    @api.model
    def create(self, vals):
        if (vals.get('compute_price') == 'fixed') and vals.get('fixed_price') <= 0:
            raise UserError("Price List Item value must be greater than zero.")

        if (vals.get('compute_price')  == 'percentage') and vals.get('percent_price') <= 0:
            raise UserError("Price List Item value must be greater than zero.")

        return super(AffiliateProductPricelistItem,self).create(vals)

    # @api.model
    # def create(self, vals):
    #     if vals.get('fixed_price') and vals.get('fixed_price') < 0:
    #         raise UserError(_("Fixed Price should not be in negative figure."))
    #     if vals.get('percent_price') and vals.get('percent_price') > -1  or vals.get('percent_price') < 100:
    #         raise UserError(_("Percentage Price should not be less than zero or greater than 100."))
    #     return super(AffiliateProductPricelistItem,self).create(vals)
