# -*- coding: utf-8 -*-

from openerp import models, fields, api

from error import Error

class Products(models.Model):
    _inherit = 'product.product'

    @api.model
    def get_picking_order(self,barcode):
        attr=[('barcode','=',barcode)]
        product = self.search(attr)
        if len(product)==0:
            err = Error()
            err.set_error_msg("Barcode Inesistente")
            return err

        #trovo le "spedizioni" (stock.picking) che contengono il prodotto
        #controllo le righe di spedizione
        #scelgo quelle che sono in uscita
        line = self.env['stock.pack.operation']
        attr = [('product_id','=',product.id),('picking_id.picking_type_code','=','outgoing')]
        picking_line = line.search(attr)

        if len(picking_line)==0:
            err = Error()
            err.set_error_msg("Nessun ordine di spedizione con questo prodotto")
            return err

        for single_line in picking_line:
            print single_line.picking_id.picking_type_code

        return product
