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
    def get_allocation(self):
        result = self.env['netaddiction.wh.locations.line'].search([('product_id','=',self.id)],order='wh_location_id')
        if len(result)==0:
            err = Error()
            err.set_error_msg("Prodotto non presente nel magazzino")
            return err

        return result

    ########################
    #INVENTORY APP FUNCTION#
    #ritorna un dict simile#
    #ad un json per il web #
    ########################
    @api.model
    def check_product(self,barcode):
        product = self._get_product_from_barcode(barcode)
        if isinstance(product,Error):
            return {'result' : 0, 'error' : product.get_error_msg()}

        return {'result' : 1 , 'product_id' : product.id}


    @api.model
    def get_json_allocation(self,barcode):
        """
        ritorna un json con i dati per la ricerca per porodotto
        """
        product = self._get_product_from_barcode(barcode)  

        if isinstance(product,Error):
            return {'result' : 0, 'error' : product.get_error_msg()}

        results = product.get_allocation()

        if isinstance(results,Error):
            return {'result' : 0, 'error' : results.get_error_msg()}

        allocations = {
            'result' : 1,
            'product' : product.display_name,
            'barcode' : product.barcode,
            'product_id' : product.id,
            'allocations' : []
        }
        for res in results:
            allocations['allocations'].append({'shelf':res.wh_location_id.name,'qty':res.qty, 'line_id': res.id})

        return allocations

    ############################
    #END INVENTORY APP FUNCTION#
    ############################

    
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