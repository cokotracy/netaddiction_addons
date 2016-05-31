# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date, datetime
from dateutil import relativedelta
import time, json
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from error import Error

from collections import defaultdict

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'


    count_picking_ready = fields.Integer(compute="_get_picking_out_count")
    count_picking_draft = fields.Integer(compute="_get_picking_out_count")
    count_picking_waiting = fields.Integer(compute="_get_picking_out_count")
    count_picking_late = fields.Integer(compute="_get_picking_out_count")
    count_picking_backorders = fields.Integer(compute="_get_picking_out_count")
    rate_picking_late = fields.Integer(compute="_get_picking_out_count")
    rate_picking_backorders = fields.Integer(compute="_get_picking_out_count")
    count_picking = fields.Integer(compute="_get_picking_out_count")

    @api.one
    def _get_picking_out_count(self):
        """
        Sostituisce la funziona di conteggio di default di odoo.
        In questa versione se l'ordine di vendita risulta nello stato 'DONE' non appare
        gli ordini da dover "processare" e mettere in lista prelievo
        """
        obj = self.env['stock.picking']
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', 'in', ('assigned', 'partially_available'))],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
            'count_picking_late': [('min_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting', 'partially_available'))],
        }
        result = {}
        for field in domains:
            data = obj.search( domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)])
            count=len(data)
            for pick in data:
                if len(pick.sale_id)>0:
                    if pick.sale_id.state =='done':
                        count = count -1

            for tid in self.ids:
                self.update({field:count})


class StockPickingWave(models.Model):
    _inherit = 'stock.picking.wave'

    in_exit = fields.Boolean(string="In uscita",default=False) #FORSE DA CAMBIARE IN_ENTRATA (in realtà se true è una lista purchase)
    reverse_supplier = fields.Boolean(string="Resi a Fornitore",default=False) 

    @api.multi
    def get_product_list(self):
        """
        ritorna la lista dei prodotti e le quantità da pickuppare
        """
        scraped_type = self.env['netaddiction.warehouse.operations.settings'].search([('company_id','=',self.env.user.company_id.id),('netaddiction_op_type','=','reverse_supplier_scraped')])
        wh = scraped_type.operation.default_location_src_id.id
        scrape_id = scraped_type.operation.id

        self.ensure_one()
        qtys = defaultdict(lambda: defaultdict(float))
        products = {}
        for picks in self.picking_ids:
            if picks.picking_type_id.id == scrape_id:
                is_scraped = True
            else:
                is_scraped = False

            for pick in picks.pack_operation_product_ids:
                if is_scraped is False:
                    qtys[pick.product_id.barcode]['product_qty'] += pick.product_qty
                    qtys[pick.product_id.barcode]['remaining_qty'] += pick.remaining_qty
                    qtys[pick.product_id.barcode]['qty_done'] += pick.qty_done
                    qty_scraped = 0
                else:
                    qty_scraped = pick.product_qty
                qtys[pick.product_id.barcode]['qty_scraped'] += (qty_scraped - pick.qty_done)
                qtys[pick.product_id.barcode]['scraped_wh'] = 'dif'
                products[pick.product_id] = qtys[pick.product_id.barcode]
        print products
        return products

    @api.model
    def is_in_wave(self,wave_id,product_id):
        result = self.search([('id','=',int(wave_id)),(product_id,'in','picking_ids.pack_operation_product_ids.product_id')])
        print result

    @api.model
    def close_reverse(self,wave_id):
        this_wave = self.search([('id','=',int(wave_id))])

        for out in this_wave.picking_ids:
            #se trovo almeno un rigo con qty_done > 0 allora posso validare l'ordine ed eventualmente creare il backorder
            validate = False
            for op in out.pack_operation_product_ids:
                if op.qty_done > 0:
                    validate = True

            if validate:
                if out.check_backorder(out):
                    wiz_id = self.env['stock.backorder.confirmation'].create({'pick_id': out.id})
                    wiz_id.process()
                    backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', out.id)])
                    backorder_pick.write({'wave_id' : None})
                else:
                    order = self.env['purchase.order'].search([('name','=',out.origin)])
                    order.button_done()
                out.do_new_transfer()
            else:
                out.write({'wave_id' : None})

        this_wave.done()


    ########################
    #INVENTORY APP FUNCTION#
    #ritorna un dict simile#
    #ad un json per il web #
    ########################
    @api.model
    def wave_pick_ip(self,product_barcode,shelf_id,wave_id):
        result = self.search([('id','=',int(wave_id))])
        if len(result) == 0:
            err = Error()
            err.set_error_msg("Problema nel recuperare la lista prodotti o barcode mancante")
            return err

        result.picking_ids.set_pick_up(product_barcode,shelf_id)

    ############################
    #END INVENTORY APP FUNCTION#
    ############################

    ########
    #CARICO#
    ########
    @api.model
    def create_purchase_list(self,name,picking_orders):
        """
        crea una wave purhcase, nei picking_orders prende solo quelli non completati
        """
        ids = []
        for pick in picking_orders:
            for p in pick:
                res = self.env['stock.picking'].search([('id','=',p),('state','!=','done')])
                if len(res)>0:
                    for r in res:
                        ids.append(r.id)

        attr = {
            'name' : name,
            'picking_ids' : [(6,0,ids)],
            'in_exit' : True,
        }

        new = self.create(attr)
        new.confirm_picking()

        return {'id' : new.id}

    @api.model
    def close_and_validate(self,wave):
        #prendo la locazione 0/0/0
        loc_id = self.env['netaddiction.wh.locations'].search([('barcode','=','0000000001')])
        this_wave = self.search([('id','=',int(wave))])

        for out in this_wave.picking_ids:
            #se trovo almeno un rigo con qty_done > 0 allora posso validare l'ordine ed eventualmente creare il backorder
            validate = False
            for op in out.pack_operation_product_ids:
                if op.qty_done > 0:
                    validate = True
                    self.env['netaddiction.wh.locations.line'].allocate(op.product_id.id,op.qty_done,loc_id.id)

            if validate:
                if out.check_backorder(out):
                    wiz_id = self.env['stock.backorder.confirmation'].create({'pick_id': out.id})
                    wiz_id.process()
                    backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', out.id)])
                    backorder_pick.write({'wave_id' : None})
                else:
                    order = self.env['purchase.order'].search([('name','=',out.origin)])
                    order.button_done()
                out.do_new_transfer()
            else:
                out.write({'wave_id' : None})

        this_wave.done()

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    #CAMPO PER CONTARE I PEZZI DA SPEDIRE#
    number_of_pieces = fields.Integer(string="Pezzi",compute="_get_number_of_pieces")
    total_import = fields.Float(string="Importo",compute="_get_total_import")

    @api.one
    def _get_number_of_pieces(self):
        pieces = 0
        for line in self.pack_operation_product_ids:
            pieces = pieces + line.qty_done

        self.number_of_pieces = pieces

    @api.one 
    def _get_total_import(self):
        total = 0.00
        for line in self.group_id.procurement_ids:
            total += line.sale_line_id.price_subtotal + line.sale_line_id.price_tax

        total += self.carrier_price *1.22
        self.total_import = total
    ########################
    #INVENTORY APP FUNCTION#
    #ritorna un dict simile#
    #ad un json per il web #
    ########################
    @api.multi
    def set_pick_up(self,product_barcode,shelf_id):
        """
        per ogni stock picking eseguo
        """
        scraped_type = self.env['netaddiction.warehouse.operations.settings'].search([('company_id','=',self.env.user.company_id.id),('netaddiction_op_type','=','reverse_supplier_scraped')])
        wh = scraped_type.operation.default_location_src_id.id
        scrape_id = scraped_type.operation.id

        if shelf_id == 'dif':
            product_lines = []
            for pick in self:
                if pick.picking_type_id.id == scrape_id:
                    product_lines += ([x for x in pick.pack_operation_product_ids if x.product_id.barcode == product_barcode])
            for line in product_lines:       
                line.write({'qty_done': line.product_qty})
        else:
            product_lines = []
            for pick in self:
                product_lines += ([x for x in pick.pack_operation_product_ids if x.product_id.barcode == product_barcode])
            for line in product_lines:
                qty_line = int(line.product_qty) - int(line.qty_done)
                for shelf in line.product_id.product_wh_location_line_ids:
                    #se i ripiani sono uguali significa che devo scalare la quantità
                    if shelf.wh_location_id.id == int(shelf_id):
                        if qty_line < int(shelf.qty):
                            shelf.write({'qty' : shelf.qty - qty_line})
                            line.write({'qty_done': line.qty_done + float(qty_line)})
                            qty_line = 0
                        elif qty_line == int(shelf.qty):
                            shelf.unlink()
                            line.write({'qty_done': line.qty_done + float(qty_line)})
                            qty_line = 0
                        else:
                            qty_line = qty_line - int(shelf.qty)
                            line.write({'qty_done': float(shelf.qty)})
                            shelf.unlink()



    ############################
    #END INVENTORY APP FUNCTION#
    ############################

    

    @api.model 
    def create_reverse(self,attr,order_id):
        #INIZIO CREAZIONE NOTA DI CREDITO
        order = self.env['sale.order'].search([('id','=',int(order_id))])
        
        pids = {}
        count = {}
        #si prende i prodotti e le quantità di ogni rigo picking segnato come reso
        for line in attr['pack_operation_product_ids']:
            pids[int(line[2]['product_id'])] = line[2]['product_qty']
            count[int(line[2]['product_id'])] = line[2]['product_qty']

        #trova le fatture per quell'ordine con quei prodotti
        invoices = self.env['account.invoice'].search([('origin','=',order.name),('invoice_line_ids.product_id','in',pids.keys())])
        
        #per ogni rigo fattura controlla che quel prodotto si presente tra i prodotti resi
        #Lavora le quantità in modo da poter modificare la nota di credito creata con i dati corretti
        #in to_credit ritorna gli id delle fatture su cui effettuare le note di credito
        to_credit = []
        for inv in invoices:
            for line in inv.invoice_line_ids:
                if line.product_id.id in count.keys():
                    if count[line.product_id.id] <= line.quantity:
                        to_credit.append(inv)
                        count.pop(line.product_id.id)
                    else:
                        to_credit.append(inv)
                        count[line.product_id.id] -= line.quantity
        to_credit = set(to_credit)

        #per ogni fattura trovata create la nota di credito in data odierna
        #analizza le righe fattura per correggere i dati dei prodotti con quelli estratti precedentemente
        for inv in to_credit:
            ids = inv.refund(datetime.now(),datetime.now(),'Reso per ordine %s' % inv.origin)
            for i in ids:
                for line in i.invoice_line_ids:
                    if line.product_id.id in pids.keys() and pids[line.product_id.id]>0:
                        if pids[line.product_id.id] == line.quantity:
                            pids[line.product_id.id] = 0
                        elif pids[line.product_id.id] < line.quantity:
                            line.write({'quantity' : pids[line.product_id.id]})
                            pids[line.product_id.id] = 0
                        else:
                            pids[line.product_id.id] -= line.quantity
                    else:
                        line.unlink()
        #FINE CREAZIONE NOTA DI CREDITO

        obj = self.create(attr)
        obj.action_confirm()
        for line in obj.pack_operation_product_ids:
            line.write({'qty_done' : line.product_qty})

        obj.do_new_transfer()

        move = self.env['stock.move'].search([('picking_id','=',obj.id)])
        move.write({'origin' : obj.origin})

    @api.model
    def create_supplier_reverse(self,products,supplier,operations):
        """
        crea i picking per il reso a fornitore.
        products è un oggetto passato dal client products = {scraped:array[id:qta],commercial:array[id:qta]}
        supplier è l'id del fornitore a cui fare il reso.
        """   
        supplier = self.env['res.partner'].search([('id','=',int(supplier))])

        products = json.loads(products)
        operations = json.loads(operations)
        
        wh = operations['reverse_supplier']['default_location_src_id'][0]
        supp_wh = operations['reverse_supplier']['default_location_dest_id'][0]
        scraped_wh = operations['reverse_supplier_scraped']['default_location_src_id'][0]

        scrape_type = operations['reverse_supplier_scraped']['operation_type_id']
        commercial_type = operations['reverse_supplier']['operation_type_id']

        #prendo in esame i resi difettati
        pack_operation_scrapeds = []

        if len(products['scraped']) > 0:
            for prod in products['scraped']:
                line = (0,0,{
                    'product_id' : int(prod['pid']),
                    'product_qty' : int(prod['qta']),
                    'location_id' : int(scraped_wh),
                    'location_dest_id' : int(supp_wh),
                    'product_uom_id' : 1
                });

                pack_operation_scrapeds.append(line)

        #prendo in esame i resi commerciali
        pack_operation_commercial = []
        if len(products['commercial']) > 0:
            for prod in products['commercial']:
                line = (0,0,{
                    'product_id' : int(prod['pid']),
                    'product_qty' : int(prod['qta']),
                    'location_id' : int(wh),
                    'location_dest_id' : int(supp_wh),
                    'product_uom_id' : 1
                });
                pack_operation_commercial.append(line)

        #preparo gli attributi per il picking
        pick_scrape = {
                'partner_id' : int(supplier),
                'origin' : 'Reso a Fornitore Difettati %s' % supplier.name,
                'location_dest_id' : int(supp_wh),
                'picking_type_id' : scrape_type,
                'location_id' : int(scraped_wh),
                'pack_operation_product_ids' : pack_operation_scrapeds,
            }

        pick_commercial = {
                'partner_id' : int(supplier),
                'origin' : 'Reso a Fornitore Commerciali %s' % supplier.name,
                'location_dest_id' : int(supp_wh),
                'picking_type_id' : commercial_type,
                'location_id' : int(wh),
                'pack_operation_product_ids' : pack_operation_commercial,
            }

        ids = []

        if len(products['scraped']) > 0:
            obj = self.create(pick_scrape)
            obj.action_confirm()
            ids.append(obj.id)
        if len(products['commercial']) > 0:
            obj = self.create(pick_commercial)
            obj.action_confirm()
            ids.append(obj.id)


        wave = {
            'name' : 'Reso a Fornitore %s' % supplier.name,
            'picking_ids' : [(6,0,ids)],
            'reverse_supplier' : True,
        }

        wl = self.env['stock.picking.wave'].create(wave)
        wl.write({'name' : wl.name + ' - %s' % wl.id})



class StockOperation(models.Model):
    _inherit = 'stock.pack.operation'

    ########
    #CARICO#
    ########
    @api.model
    def complete_operation(self,ids,qta):
        """
        completa le righe dell'ordine di consegna in entrata per il carico
        in base alla qta passata per il prodotto presente nelle righe (ids)
        """
        operations = self.search([('id','in',ids)])
        to_remove = qta
        for op in operations:
            residual = int(op.product_qty) - int(op.qty_done)
            if residual >= to_remove:
                op.write({'qty_done' : op.qty_done + to_remove})
                to_remove = 0
                break
            if residual < to_remove:
                op.write({'qty_done' : op.qty_done + residual})
                to_remove = to_remove - residual
