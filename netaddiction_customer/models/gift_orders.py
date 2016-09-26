# -*- coding: utf-8 -*-
from openerp import api, fields, models


class GiftOrder(models.Model):
    _inherit = 'sale.order'

    gift_discount = fields.Float(string='sconto gift', default=0.0)
    gift_set_by_bo = fields.Boolean(default=False)

    def _compute_gift_amount(self, amount_total):
        if self.state == 'draft':
            if self.gift_set_by_bo:
                return (self.gift_discount, amount_total - self.gift_discount)

            if self.partner_id.got_gift:
                tot = 0.0
                for ol in self.order_line:
                    if ol.product_id.sale_ok:
                        tot += ol.price_total

                # self.gift_discount = tot if self.partner_id.total_gift > tot else self.partner_id.total_gift
                tot = tot if self.partner_id.total_gift > tot else self.partner_id.total_gift

                # self.amount_total -= self.gift_discount
                return (tot, amount_total - tot)
            else:
                return False
        else:
            if self.gift_discount > 0.0:
                return (self.gift_discount, amount_total - self.gift_discount)
            else:
                return False

    @api.onchange('gift_discount')
    def gift_changed(self):
        self.gift_set_by_bo = True
        
    @api.constrains('gift_discount')
    def _check_active(self):
        if self.gift_set_by_bo:
            attr = {
                'subject': 'Assegnazione gift',
                'message_type': 'notification',
                'model': 'sale.order',
                'res_id': self.id,
                'body': "gift assegnati %s da %s" % (self.gift_discount, self.env.user.name),
                'subtype_id': self.env.ref("mail.mt_note").id
            }
            self.env['mail.message'].create(attr)


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
