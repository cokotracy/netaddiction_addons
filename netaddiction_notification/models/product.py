# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Products(models.Model):
    _inherit = 'product.product'

    #prendo ogni dato e lo butto in notifica
    @api.multi
    def write(self,values):
        for product in self:
            msg = ''
            for key,value in values.items():
                msg = msg + "<p>"+str(key)+": "+str(product[key])+" -> "+str(value)+"</p>"
            attr = {
                'subtype_id' : 2,
                'res_id' : product.id,
                'body' : msg,
                'model' : 'product.product',
                'author_id' : self.env.user.partner_id.id,
                'message_type' : 'comment',
            }
            self.env['mail.message'].create(attr)

        return super(Products, self).write(values)
