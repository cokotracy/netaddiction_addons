# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date, datetime
from dateutil import relativedelta
import time, json
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from error import Error
from openerp.exceptions import ValidationError
import base64
from collections import defaultdict
import io
import csv

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

    product_list = fields.Many2many(string="Movimenti", comodel_name="stock.pack.operation", compute="_get_list_product")
    product_list_product = fields.Many2many(string="Prodotti caricati/scaricati", comodel_name="product.product", compute="_get_list_product")

    supplier = fields.Many2one(string="Fornitore", default=False, comodel_name="res.partner", compute="_get_suppliers", search="_search_supplier")
    date_done = fields.Datetime(string="Data", default=False, compute="_get_date", search="_search_date")

    @api.one
    def _get_date(self):
        date = False
        for pick in self.picking_ids:
            date = pick.date_done
            break
        self.date_done = date

    def _search_date(self, operator, value):
        domain = [('picking_ids.date_done', operator, value)]
        return domain

    @api.one
    def _get_suppliers(self):
        # lo so è all'inverso ma non mi rompete le palle - Matteo -
        if self.in_exit:
            sup = False
            for pick in self.picking_ids:
                sup = pick.partner_id.id
                break
            self.supplier = sup

    def _search_supplier(self, operator, value):
        assert operator in ('=', 'ilike', 'like'), 'Dominio invalido per il fornitore'

        domain = [('picking_ids.partner_id.name', 'ilike', value), ('in_exit', '=', True)]
        result = self.search(domain)
        ids = []
        for res in result:
            ids.append(res.id)

        return [('id', 'in', ids)]

    @api.one
    def _get_list_product(self):
        products = []
        pids = []

        for pick in self.picking_ids:
            for operation in pick.pack_operation_product_ids:
                if operation.qty_done > 0:
                    products.append(operation.id)
                    pids.append(operation.product_id.id)

        self.product_list = [(6, False, products)]
        self.product_list_product = [(6, False, pids)]

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
       
        return products

    @api.model
    def is_in_wave(self,wave_id,product_id):
        result = self.search([('id','=',int(wave_id)),(product_id,'in','picking_ids.pack_operation_product_ids.product_id')])
        

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
    def wave_pick_ip(self,product_barcode,shelf_id,wave_id,qty_to_down):
        result = self.search([('id','=',int(wave_id))])
        if len(result) == 0:
            err = Error()
            err.set_error_msg("Problema nel recuperare la lista prodotti o barcode mancante")
            return err
        
        test = int(qty_to_down)

        if shelf_id == 'dif':
            for res in result.picking_ids:
                res.pick_up_scraped(product_barcode,qty_to_down)
        else:
            for res in result.picking_ids:
                if test > 0:
                    picked_qty = res.set_pick_up(product_barcode,shelf_id,test)
                    test -= int(picked_qty[0])
                

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
                    op.product_id.qty_limit = 0

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

    barcode_image = fields.Text(
        string='Barcode image',
        compute='_compute_barcode_image',
    )

    @api.one
    def _compute_barcode_image(self):
        barcode = self.env['report'].barcode('Code128',
                self.delivery_barcode,
                width=448,
                height=50,
                humanreadable=0)
        barcode_base64 = base64.b64encode(barcode)
        self.barcode_image = 'data:image/png;base64,' + barcode_base64

    @api.multi
    def action_cancel(self):
        contrassegno = self.env.ref('netaddiction_payments.contrassegno_journal')
        cancel = []
        posted = []
        for pick in self:
            if pick.delivery_read_manifest:
                raise ValidationError("Non puoi annullare la spedizione in quanto è già in carico al corriere")
            else:
                if pick.payment_id.state != 'posted':
                    #cancello tutto
                    cancel.append(pick.payment_id)
                    
                else:
                    products = []
                    for pl in pick.move_lines:
                        products.append(pl.product_id.id)
                    for plo in pick.pack_operation_product_ids:
                        products.append(plo.product_id.id)

                    for inv in pick.payment_id.invoice_ids:
                        ref = inv.refund(datetime.now(),datetime.now(),'Annullata spedizione %s ' % pick.name)
                        for line in ref.invoice_line_ids:
                            if line.product_id.id not in products:
                                line.unlink()
                        ref.compute_taxes()
                        ref._compute_amount()

                        account_id = self.env['account.account'].search([('code','=',410100),('company_id','=',self.env.user.company_id.id)])
                        carrier_line = {
                            'product_id' : pick.carrier_id.product_id.id,
                            'quantity' : 1,
                            'price_unit' : pick.total_import - ref.amount_total,
                            'name' : pick.carrier_id.product_id.name,
                            'account_id' : account_id.id,
                            'invoice_line_tax_ids' : [(6,False,[pick.carrier_id.product_id.taxes_id.id])],
                            'invoice_id':ref.id
                        }
                        
                        self.env['account.invoice.line'].create(carrier_line)

                        ref.compute_taxes()
                        ref._compute_amount()

       

        for can in cancel:
            can.invoice_ids.write({'state':'cancel'})
            can.unlink()

        return super(StockPicking,self).action_cancel()

    @api.multi
    def open_website_url(self):
        self.ensure_one()
        brt = self.env.ref('netaddiction_warehouse.carrier_brt').id

        if self.carrier_id.id == brt:
            url = 'http://as777.bartolini.it/vas/sped_det_show.hsm?referer=sped_numspe_par.htm&ChiSono=%s' % self.delivery_barcode
        else:
            url = 'https://www.mysda.it/SDAServiziEsterniWeb2/faces/SDAElencoSpedizioni.jsp?user=NETA20&idritiro=%s' % self.delivery_barcode

        client_action = {'type': 'ir.actions.act_url',
                         'name': "Shipment Tracking Page",
                         'target': 'new',
                         'url': url,
                         }
        return client_action

    @api.one
    def _get_number_of_pieces(self):
        pieces = 0
        for line in self.pack_operation_product_ids:
            pieces = pieces + line.qty_done

        self.number_of_pieces = pieces


    @api.one 
    def _get_total_import(self):
        total = 0.00
        pp_aj = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal').id
        sofort_aj = self.env['ir.model.data'].get_object('netaddiction_payments', 'sofort_journal').id
        if self.payment_id and self.payment_id.journal_id.id not in (pp_aj, sofort_aj):
            self.total_import = self.payment_id.amount

        else:
            for line in self.group_id.procurement_ids:
                total += line.sale_line_id.price_subtotal + line.sale_line_id.price_tax
        
            res = self.carrier_id.product_id.taxes_id.compute_all(self.carrier_price)        

            total += res['total_included']
        
            method_contrassegno_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal').id
            if self.sale_order_payment_method.id == method_contrassegno_id:
                contrassegno = self.env.ref('netaddiction_payments.product_contrassegno')
                res_c = self.carrier_id.product_id.taxes_id.compute_all(contrassegno.list_price)
                total += res_c['total_included']

            if self.sale_id.gift_discount > 0.0:
                gift = self.env["netaddiction.gift_invoice_helper"].compute_gift_value(self.sale_id.gift_discount, self.sale_id.amount_total, total)
                total -= gift

            self.total_import = total
    ########################
    #INVENTORY APP FUNCTION#
    #ritorna un dict simile#
    #ad un json per il web #
    ########################
    @api.one 
    def pick_up_scraped(self,product_barcode,qty_to_down):
        scraped_type = self.env['netaddiction.warehouse.operations.settings'].search([('company_id','=',self.env.user.company_id.id),('netaddiction_op_type','=','reverse_supplier_scraped')])
        wh = scraped_type.operation.default_location_src_id.id
        scrape_id = scraped_type.operation.id

        product_lines = [] 
        if self.picking_type_id.id == scrape_id:
            product_lines += ([x for x in self.pack_operation_product_ids if x.product_id.barcode == product_barcode])
        for line in product_lines:       
            line.write({'qty_done': line.product_qty})

    @api.one
    def set_pick_up(self,product_barcode,shelf_id,qty_to_down):
        """
        per ogni stock picking eseguo
        """
               
        product_lines = ([x for x in self.pack_operation_product_ids if x.product_id.barcode == product_barcode])
        qty = 0
        test = int(qty_to_down)

        for line in product_lines:
            shelf = self.env['netaddiction.wh.locations.line'].search([('product_id','=',line.product_id.id),('wh_location_id','=',int(shelf_id))])
            if len(shelf) == 0:
                raise ValidationError("Ripiano inesistente")

            qty_line = int(line.product_qty) - int(line.qty_done)
            
            if test > 0:
                if int(qty_line) <= test:
                    shelf.write({'qty' : shelf.qty - int(qty_line)})
                    line.write({'qty_done': line.qty_done + float(qty_line)})
                    test = test - qty_line
                    qty = qty + qty_line
                    qty_line = 0
                    if shelf.qty == 0:
                        shelf.unlink()
                else:
                    shelf.write({'qty' : shelf.qty - int(test)})
                    line.write({'qty_done': line.qty_done + float(test)})
                    qty = qty + test
                    test = 0
                    if shelf.qty == 0:
                        shelf.unlink()
        
        return qty              



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
            ids.origin = inv.number
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


class StockQuant(models.Model):
    _inherit='stock.quant'

    @api.model
    def inventory_csv(self):
        wh = self.env.ref('stock.stock_location_stock').id
        results = self.search([('location_id', '=', wh)])
        products = {}
        for res in results:
            if res.product_id.id in products:
                products[res.product_id.id]['qty'] += int(res.qty)
                products[res.product_id.id]['inventory_value'] += round(res.inventory_value, 2)
            else:
                products[res.product_id.id] = {
                    'name': res.product_id.display_name,
                    'category': res.product_id.categ_id.display_name,
                    'qty': int(res.qty),
                    'inventory_value': round(res.inventory_value, 2),
                }
                text = ''
                for loc in res.product_id.product_wh_location_line_ids:
                    text += '| %s - %s |' % (loc.wh_location_id.name, loc.qty)

                products[res.product_id.id]['location'] = text

        output = io.BytesIO()
        writer = csv.writer(output)
        csvdata = ['Categoria', 'Prodotto', 'Quantità', 'Valore Totale', 'Scaffali']
        writer.writerow(csvdata)
        for product in products:
            csvdata = [products[product]['category'].encode('utf8'), products[product]['name'].encode('utf8'), products[product]['qty'], products[product]['inventory_value'], products[product]['location']]
            writer.writerow(csvdata)
        data = base64.b64encode(output.getvalue()).decode()
        output.close()
        attr = {
            'name': 'export %s' % date.today(),
            'type': 'binary',
            'datas': data
        }
        return self.env['ir.attachment'].create(attr)

    @api.model
    def get_quant_from_supplier(self,supplier_id):
        wh = self.env.ref('stock.stock_location_stock')
        result = self.search([('company_id','=',self.env.user.company_id.id),('location_id','=',wh.id),
            ('history_ids.picking_id.partner_id.id','=',int(supplier_id)),('reservation_id','=',False)])
        quants = {}
        for res in result:
            if res.product_id.id in quants:
                quants[res.product_id.id]['qty']+=res.qty
                #quants[res.product_id]['inventory_value']+=res.inventory_value
            else:
                quants[res.product_id.id] = {
                    'id':res.product_id.id,
                    'name':res.product_id.display_name,
                    'qty':res.qty,
                    #'inventory_value':res.inventory_value
                }
        return quants

    @api.model
    def get_scraped_from_supplier(self,supplier_id):
        scraped_stock = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','=','reverse_scrape'),('company_id','=',self.env.user.company_id.id)])
        wh = scraped_stock.operation.default_location_dest_id.id
        result = self.search([('company_id','=',self.env.user.company_id.id),('location_id','=',wh),
            ('history_ids.picking_id.partner_id.id','=',int(supplier_id)),('reservation_id','=',False)])
        quants = {}
        for res in result:
            if res.product_id.id in quants:
                quants[res.product_id.id]['qty']+=res.qty
                #quants[res.product_id]['inventory_value']+=res.inventory_value
            else:
                quants[res.product_id.id] = {
                    'id':res.product_id.id,
                    'name':res.product_id.display_name,
                    'qty':res.qty,
                    #'inventory_value':res.inventory_value
                }
        return quants

    def _prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        if context.get('force_valuation_amount'):
            valuation_amount = context.get('force_valuation_amount')
        else:
            if move.product_id.cost_method == 'average':
                valuation_amount = cost if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal' else move.product_id.standard_price
            else:
                valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
        #the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        #the company currency... so we need to use round() before creating the accounting entries.
        valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
        #check that all data is correct
        #if move.company_id.currency_id.is_zero(valuation_amount):
        #    raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (move.product_id.name,))
        partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(move.picking_id.partner_id).id) or False
        debit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'partner_id': partner_id,
                    'debit': valuation_amount > 0 and valuation_amount or 0,
                    'credit': valuation_amount < 0 and -valuation_amount or 0,
                    'account_id': debit_account_id,
        }
        credit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'partner_id': partner_id,
                    'credit': valuation_amount > 0 and valuation_amount or 0,
                    'debit': valuation_amount < 0 and -valuation_amount or 0,
                    'account_id': credit_account_id,
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
