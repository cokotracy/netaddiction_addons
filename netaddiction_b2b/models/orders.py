# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class Order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def delivery_set(self):
        super(Order,self).delivery_set()

        for order in self:
            if order.pricelist_id.id != 1:
                price = order.pricelist_id.carrier_price
                gratis = order.pricelist_id.carrier_gratis 	
                order.carrier_id = order.pricelist_id.carrier_id.id

                if order.amount_total - order.delivery_price > gratis:
                    price_unit = 0.00
                else:
                    price_unit = price	

                line = self.env['sale.order.line'].search([('is_delivery','=',True),('order_id','=',order.id)])

                line.price_unit = float(price_unit)
                line.product_id = order.pricelist_id.carrier_id.product_id.id
                line.name = order.pricelist_id.carrier_id.name

                order.delivery_price = price_unit