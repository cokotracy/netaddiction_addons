# -*- coding: utf-8 -*-

from openerp import api, models


class Products(models.Model):
    _inherit = 'product.product'

    @api.multi
    def write(self, values):
        if self.env.context.get('skip_products_log_tracking', False):
            return super(Products, self).write(values)

        old_intax = {}
        for product in self:
            log_line = self.env["netaddiction.log.line"]
            if 'sale_ok' in values and values['sale_ok'] != product.sale_ok:
                log_line.sudo().create(log_line.create_tracking_values(product.sale_ok, values['sale_ok'], 'sale_ok', 'boolean', 'product.product', product.id, self.env.uid, product.company_id.id, object_name=product.name))
            if 'available_date' in values and values['available_date'] != product.available_date:
                log_line.sudo().create(log_line.create_tracking_values(product.available_date, values['available_date'], 'available_date', 'date', 'product.product', product.id, self.env.uid, product.company_id.id, object_name=product.name))
            if 'out_date' in values and values['out_date'] != product.out_date:
                log_line.sudo().create(log_line.create_tracking_values(product.out_date, values['out_date'], 'out_date', 'date', 'product.product', product.id, self.env.uid, product.company_id.id, object_name=product.name))
            if 'final_price' in values:
                log_line.sudo().create(log_line.create_tracking_values(product.final_price, values['final_price'], 'final_price', 'float', 'product.product', product.id, self.env.uid, product.company_id.id, object_name=product.name))
                old_intax[product.id] = product.intax_price
            if 'special_price' in values:
                log_line.sudo().create(log_line.create_tracking_values(product.special_price, values['special_price'], 'special_price', 'float', 'product.product', product.id, self.env.uid, product.company_id.id, object_name=product.name))
                old_intax[product.id] = product.intax_price

        res = super(Products, self).write(values)

        if old_intax:
            for product in self:
                if product.id in old_intax:
                    log_line.sudo().create(log_line.create_tracking_values(old_intax[product.id], product.intax_price, 'intax_price', 'float', 'product.product', product.id, self.env.uid, product.company_id.id, object_name=product.name))
        return res
