# -*- coding: utf-8 -*-

from openerp import models, fields, api

from error import Error

class Products(models.Model):
    _inherit = 'product.product'

    @api.model
    def _get_product_from_barcode(self,barcode):
        attr=[('barcode','=',barcode)]
        product = self.search(attr)
        if len(product)==0:
            err = Error()
            err.set_error_msg("Barcode Inesistente")
            return err

        return product

    @api.model
    def get_allocation(self,barcode):
        product = self._get_product_from_barcode(barcode)  

        if isinstance(product, Error):
            return product

        pid = product.id
        result = self.env['netaddiction.wh.locations.line'].search([('product_id','=',pid)],order='wh_location_id')
        if len(result)==0:
            err = Error()
            err.set_error_msg("Prodotto non presente nel magazzino")
            return err

        return result

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

    #########
    #PICK UP#
    #########
    @api.multi 
    def get_shelf_to_pick(self,qty):
        """
        Passando la quantità da pickuppare (qty), la funzione restituisce il/i ripiano/i 
        da cui scaricare il prodotto in totale autonomia
        ritorna una lista di dict {'location_id','quantità da scaricare'}
        """
        self.ensure_one()
        shelf = {}
        for alloc in self.product_wh_location_line_ids:
            if qty>0:
                if qty <= alloc.qty:
                    shelf[alloc.wh_location_id] = int(qty) 
                    qty = 0
                else:
                    shelf[alloc.wh_location_id] = int(alloc.qty) 
                    qty = int(qty) - int(alloc.qty)

        return shelf

