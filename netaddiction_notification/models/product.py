# -*- coding: utf-8 -*-

from openerp import models, fields, api
from base_class import Notification

class Products(models.Model,Notification):
    _inherit = 'product.product'

    @api.multi
    def write(self,values):
        self._save_msg(self,values)
        return super(Products, self).write(values)

    def message_related_field(self,older,new):
        d = {}
        prima = []
        dopo=[]
        msg = ''
        for old in older:
            d['Fornitore'] = str(old.name.name)
            d['Codice Fornitore'] = str(old.product_code)
            d['Quantita Disponibile'] = old.avail_qty
            d['Prezzo'] = old.price
            prima.append(d)

        for n in new:
            line_id = n[1]
            searched = [('id','=',line_id)]
            result = self.env['product.supplierinfo'].search(searched)
            if n[2]:
                attr={k: v for k, v in n[2].items() if k in ['name','product_code','avail_qty','price']}
                # TODO: gestire meglio le aggiunte di fornitori e i nomi degli attributi
                # in questo caso non prende il nome ma l'id del res partner
                if len(result)>0:
                    searched = [('id','=',attr['name'])]
                    res = self.env['res.partner'].search(searched)
                    attr['name'] = str(res.name)
                dopo.append(attr)
            else:
                dopo.append('tolto fornitore '+str(result.name.name))

        msg = msg + " <br> " + str(prima) + " <br>--------------<br> " + str(dopo)

        return msg
