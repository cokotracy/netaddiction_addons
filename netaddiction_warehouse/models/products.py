# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
from error import Error

class Products(models.Model):
    _inherit = 'product.product'

    days_available = fields.Integer(string="Disponibile Tra (in giorni)",help="Calcola tra quanto potrebbe essere disponibile, se zero è disponibile immediatamente",
            compute="_get_days_available")

    @api.one 
    def _get_days_available(self):
        today = datetime.date.today()
        self.days_available = self.calculate_days_available(self.qty_available_now)

    @api.multi
    def calculate_days_available(self,qty):
        """funzione di appoggio che calcola la disponibilità del prodotto in base ad una ipotetica quantità che gli
        viene passata, ad esempio se vuoi comprare 2 qty di un prodotto a disponibilità 1 ti dice eventualmente
        la seconda quantità quando potrebbe essere consegnata"""
        today = datetime.date.today()
        self.ensure_one()
        if qty>0:
            return 0
        else:
            #per prima cosa controllo la data di uscita
            if self.out_date is not False and datetime.datetime.strptime(self.out_date,"%Y-%m-%d").date() > datetime.date.today():
                return (datetime.datetime.strptime(self.out_date,"%Y-%m-%d").date() - today).days
            else:
                if self.available_date is not False and datetime.datetime.strptime(self.available_date,"%Y-%m-%d").date() > datetime.date.today():
                    return (datetime.datetime.strptime(self.available_date,"%Y-%m-%d").date() - today).days
                else:
                    #controllo i fornitori
                    #prendo il fornitore a priorità più alta (se ce ne sono due con la stessa priorità prendo quello a prezzo più basso)
                    supplier = 0
                    this_priority = 0
                    price = 0
                    #qua uso sudo per dare la possibilità di leggere questo campo
                    #anche a chi non ha i permessi sui fornitori
                    for sup in self.sudo().seller_ids:
                        if int(sup.name.supplier_priority) > int(this_priority):
                            supplier = sup
                            this_priority = sup.name.supplier_priority
                            price = sup.price
                        else:
                            if int(sup.name.supplier_priority) == int(this_priority) and float(sup.price) < float(price):
                                supplier = sup
                                this_priority = sup.name.supplier_priority
                                price = sup.price

                    if supplier == 0:
                        return 99
                    else:
                        return int(supplier.delay)


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