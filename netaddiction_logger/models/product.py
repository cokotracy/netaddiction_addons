# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools


class Products(models.Model):
    _inherit = 'product.product'


    @api.multi
    def write(self,values):
        for product in self:
            log_line = self.env["netaddiction.log.line"]
            if 'sale_ok' in values and values['sale_ok'] and not product.sale_ok:
                log_line.sudo().create(log_line.create_tracking_values(product.sale_ok, values['sale_ok'], 'sale_ok', 'boolean', 'product.product', product.id, self.env.uid,object_name=product.name))
            if 'available_date' in values and values['available_date'] != product.available_date:
                log_line.sudo().create(log_line.create_tracking_values(product.available_date, values['available_date'], 'available_date', 'date', 'product.product', product.id, self.env.uid, object_name=product.name))
            if 'final_price' in values:
                log_line.sudo().create(log_line.create_tracking_values(product.final_price, values['final_price'], 'final_price', 'float', 'product.product', product.id, self.env.uid,object_name=product.name))
            if 'special_price' in values:
                log_line.sudo().create(log_line.create_tracking_values(product.special_price, values['special_price'], 'special_price', 'float', 'product.product', product.id, self.env.uid,object_name=product.name))


        return super(Products, self).write(values)




