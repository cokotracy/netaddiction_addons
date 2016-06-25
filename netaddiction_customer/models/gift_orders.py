# -*- coding: utf-8 -*-
from openerp import models, fields, api

class GiftOrder(models.Model):
    _inherit = 'sale.order'

    gift_discount = fields.Float(string='sconto gift', default=0.0)


    @api.one
    def _compute_gift_amount(self):
        if self.partner_id.got_gift:
            tot = 0.0
            for ol in self.order_line:
                if ol.product_id.sale_ok:
                    tot += ol.price_total

            if self.state == 'draft':
                self.gift_discount = tot if self.partner_id.total_gift > tot else self.partner_id.total_gift

        self.amount_total -= self.gift_discount
       
           


    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     super(GiftOrder,self)._amount_all()
    #     for order in self:
    #         if order.partner_id.got_gift:
    #             tot = 0.0
    #             for ol in order.order_line:
    #                 if ol.product_id.sale_ok:
    #                     tot += ol.price_total
    #             order.gift_discount = tot if order.partner_id.total_gift > tot else order.partner_id.total_gift
    #             order.amount_total -= order.gift_discount

    # @api.multi
    # def action_confirm(self):
    #     super(GiftOrder,self).action_confirm()
    #     for order in self:
    #         if order.gift_discount > 0.0:
    #             order.partner_id.remove_gift_value(order.gift_discount)