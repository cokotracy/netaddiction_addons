# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date

class bi_wizard_product_bundle(models.TransientModel):
    _name = 'wizard.product.bundle.bi'
    _description = "Wizard Product Bundle"

    product_id = fields.Many2one('product.product',string='Bundle',required=True)
    product_qty = fields.Integer('Quantity',required=True ,default=1)
    product_price = fields.Float(string="Price")
    pack_ids = fields.One2many('product.pack', related='product_id.pack_ids', string="Select Products")

    def button_add_product_bundle_bi(self):
        sale_order = self.env['sale.order'].browse(self._context.get('active_id')) 
        if sale_order.pricelist_id.discount_policy == 'with_discount':
            if self.product_id.uom_id:
                price =dict((product_id, res_tuple[0]) for product_id, res_tuple in sale_order.pricelist_id._compute_price_rule([(self.product_id, self.product_qty, sale_order.partner_id)], date=False, uom_id=self.product_id.uom_id.id).items())
                pricelst_price = price.get(self.product_id.id, 0.0)
            for pack in self:
                if pack.product_id.is_pack:
                    test = self.env['sale.order.line'].create({'order_id':self._context['active_id'],
                                                    'product_id':pack.product_id.id,
                                                    'name':pack.product_id.name,
                                                    'price_unit':pricelst_price,
                                                    'product_uom':pack.product_id.uom_id.id,
                                                    'product_uom_qty': self.product_qty
                                                    })
        else:
            if self.product_id.uom_id:
                price =dict((product_id, res_tuple[0]) for product_id, res_tuple in sale_order.pricelist_id._compute_price_rule([(self.product_id, self.product_qty, sale_order.partner_id)], date=False, uom_id=self.product_id.uom_id.id).items())
                pricelst_price = price.get(self.product_id.id, 0.0)
            fix_discount = []
            product_temp_obj = self.env['product.template'].search([('name','=',self.product_id.name)],limit=1)
            for pricelist in sale_order.pricelist_id.item_ids:
                if pricelist.min_quantity <= self.product_qty:
                    if pricelist.date_end:
                        if pricelist.date_end <= date.today():
                            fix_discount.append(0.0)
                    if pricelist.applied_on == '3_global':
                        if pricelist.compute_price == 'fixed':
                            if pricelist.fixed_price < self.product_id.lst_price:
                                fixed_value = ((pricelist.fixed_price - self.product_id.lst_price)/self.product_id.lst_price)*100
                                fix_discount.append(abs(fixed_value))
                        elif pricelist.compute_price == 'percentage':
                            fix_discount.append(pricelist.percent_price)
                    elif pricelist.applied_on == '2_product_category' and pricelist.categ_id == self.product_id.categ_id.id:
                        if pricelist.compute_price == 'fixed':
                            if pricelist.fixed_price < self.product_id.lst_price:
                                fixed_value = ((pricelist.fixed_price - self.product_id.lst_price)/self.product_id.lst_price)*100
                                fix_discount.append(abs(fixed_value))
                        elif pricelist.compute_price == 'percentage':
                            fix_discount.append(pricelist.percent_price)
                    elif pricelist.applied_on == '1_product' and pricelist.product_tmpl_id.id == product_temp_obj.id:
                        if pricelist.compute_price == 'fixed':
                            if pricelist.fixed_price < self.product_id.lst_price:
                                fixed_value = ((pricelist.fixed_price - self.product_id.lst_price)/self.product_id.lst_price)*100
                                fix_discount.append(abs(fixed_value))
                        elif pricelist.compute_price == 'percentage':
                            fix_discount.append(pricelist.percent_price)
                    elif pricelist.applied_on == '0_product_variant' and pricelist.product_id == self.product_id.id:
                        if pricelist.compute_price == 'fixed':
                            if pricelist.fixed_price < self.product_id.lst_price:
                                fixed_value = ((pricelist.fixed_price - self.product_id.lst_price)/self.product_id.lst_price)*100
                                fix_discount.append(abs(fixed_value))
                        elif pricelist.compute_price == 'percentage':
                            fix_discount.append(pricelist.percent_price)
            if fix_discount:
                discount = fix_discount[0]
            else:
                discount = 0.0
            if pricelist.fixed_price > self.product_id.lst_price or pricelist.compute_price == 'formula':
                price = pricelst_price
            else:
                price = self.product_id.lst_price
                
            for pack in self:
                if pack.product_id.is_pack:
                    test = self.env['sale.order.line'].create({'order_id':self._context['active_id'],
                                                'product_id':pack.product_id.id,
                                                'name':pack.product_id.name,
                                                'price_unit':price,
                                                'discount' : discount,
                                                'product_uom':pack.product_id.uom_id.id,
                                                'product_uom_qty': self.product_qty
                                                })

        return True

    @api.onchange('product_id')
    def onchange_product(self):
        sale_order = self.env['sale.order'].browse(self._context.get('active_id')) 
        if self.product_id:
            if self.product_id.uom_id:
                price =dict((product_id, res_tuple[0]) for product_id, res_tuple in sale_order.pricelist_id._compute_price_rule([(self.product_id, self.product_qty, sale_order.partner_id)], date=False, uom_id=self.product_id.uom_id.id).items())
                pricelst_price = price.get(self.product_id.id, 0.0)
                self.product_price = pricelst_price
        else:
            pass

    @api.onchange('product_qty')
    def onchange_quantity(self):
        self.onchange_product()