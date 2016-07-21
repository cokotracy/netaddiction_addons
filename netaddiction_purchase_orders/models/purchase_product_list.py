# -*- coding: utf-8 -*-

from openerp import models, fields, api
from collections import defaultdict
from datetime import datetime,date,timedelta

class Products(models.Model):
    _inherit = "product.product"


    @api.model
    def get_qty_available_negative(self,search,supplier_id):
        result = []
        if search:
            domain = [('company_id','=',self.env.user.company_id.id),('qty_available_now','<',0),('name','ilike',str(search))]
        else:
            domain = [('company_id','=',self.env.user.company_id.id),('qty_available_now','<',0)]

        if supplier_id and supplier_id != 'all':
            domain.append(('seller_ids.name','=',int(supplier_id)))

        products = self.search(domain)
        for prod in products:
            search = self.env['purchase.order.line'].search([('product_id','=',prod.id),('state','=','draft')])
            qty = 0
            purchases = ''
            for s in search:
                qty = qty + s.product_qty
        
            attr = {
                'id' : prod.id,
                'display_name' : prod.display_name,
                'qty_available' : prod.qty_available,
                'qty_available_now' : prod.qty_available_now,
                'virtual_available' : prod.virtual_available,
                'outgoing_qty' : prod.outgoing_qty,
                'incoming_qty' : prod.incoming_qty,
                'inorder_qty' : qty,
                'seller_ids' : [],
            }

            for sup in prod.seller_ids:
                attr['seller_ids'].append({
                    'id' : sup.name.id,
                    'name' : sup.name.name,
                    'price' : sup.price,
                    'delay' : sup.delay,
                    'avail_qty' : sup.avail_qty 
                    })
            result.append(attr)
        return result

class PurchaseOrders(models.Model):
    _inherit="purchase.order"

    @api.model
    def put_in_order(self,products):
        """
        products: lista di liste [product_id,supplier_id,qty _order]
        data la lista cerca se c'è già aperto un ordine per quel fornitore e inserisce la riga corrispondente,
        altrimenti crea il nuovo ordine
        """
        organize = defaultdict(list)
        for product in products:
            supplier_id = product[1]
            organize[supplier_id].append(product)

        for supplier,prods in organize.iteritems():
            orders = self.search([('company_id','=',self.env.user.company_id.id),('state','=','draft'),('partner_id','=',int(supplier))])
            ids = self._return_attr(prods,supplier)
            
            if len(orders) == 0:
                attr = {
                    'partner_id' : int(supplier),
                    'order_line' : ids  
                }
                self.env['purchase.order'].create(attr)
            else:
                orders[0].write({'order_line':ids})
        
        return True

    def _return_attr(self,prods,supplier):
        ids = []
        for p in prods:
            prod = self.env['product.product'].search([('id','=',int(p[0]))])
            price_unit = 0.0
            name = ''
            delay = 1
            for i in prod.seller_ids:
                if i.name.id == int(supplier):
                    price_unit = i.price
                    name = i.product_name or prod.display_name
                    delay = i.delay 

                    attr = {
                        'product_id' : int(p[0]),
                        'product_qty': int(p[2]),
                        'product_uom' : prod.uom_po_id.id or prod.uom_id.id,
                        'price_unit' : float(price_unit),
                        'name' : name,
                        'date_planned' : datetime.now()+timedelta(days=int(delay))
                    }
                    ids.append((0,0,attr))   
        return ids     

