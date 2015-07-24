# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Sale_Order_Line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change( self, pricelist, product, qty=0, uom=False, qty_uos=0,
        uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False,
        packaging=False, fiscal_position=False, flag=False,context=None):
        """
        override del metodo per mettere il prezzo giusto nel campro price_unit
        della linea d'ordine dopo aver effettuato la modifica del campo lst_price
        nel modello product
        """

        result = super(Sale_Order_Line,self).product_id_change(pricelist,product,qty=qty,
            uom=uom,qty_uos=qty_uos, uos=uos,name=name,partner_id=partner_id,lang=lang,
            update_tax=update_tax,date_order=date_order,packaging=packaging,
            fiscal_position=fiscal_position,flag=flag)

        product_obj = self.env['product.product']
        product_data = product_obj.search([['id','=',product]])
        values = result['value']

        #sostituisco il price_unit con il prezzo corretto
        values.update({'price_unit' : product_data.lst_price })
        result['value']=values
        return result
