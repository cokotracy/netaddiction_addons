# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date, datetime
from dateutil import relativedelta
import time
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

    in_exit = fields.Boolean(string="In uscita",default=False)

    @api.multi
    def get_product_list(self):
        """
        ritorna la lista dei prodotti e le quantità da pickuppare
        """
        self.ensure_one()
        qtys = defaultdict(lambda: defaultdict(float))
        products = {}
        for picks in self.picking_ids:
            for pick in picks.pack_operation_product_ids:
                qtys[pick.product_id.barcode]['product_qty'] += pick.product_qty
                qtys[pick.product_id.barcode]['remaining_qty'] += pick.remaining_qty
                qtys[pick.product_id.barcode]['qty_done'] += pick.qty_done
                products[pick.product_id] = qtys[pick.product_id.barcode]

        return products

    @api.model
    def is_in_wave(self,wave_id,product_id):
        result = self.search([('id','=',int(wave_id)),(product_id,'in','picking_ids.pack_operation_product_ids.product_id')])
        print result

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

    @api.one
    def _get_number_of_pieces(self):
        pieces = 0
        for line in self.pack_operation_product_ids:
            pieces = pieces + line.qty_done

        self.number_of_pieces = pieces

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

    ################################
    #FUNCTION PER CONTROLLO PICK UP#
    ################################
    @api.model
    def do_validate_orders(self,pick_id):
        this = self.search([('id','=',int(pick_id))])
        if this.check_backorder(this):
            wiz_id = self.env['stock.backorder.confirmation'].create({'pick_id': this.id})
            wiz_id.process()
            backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', this.id)])
            backorder_pick.write({'wave_id' : None})
        else:
            order = self.env['sale.order'].search([('name','=',this.origin)])
            order.action_done()


        this.do_new_transfer()
        count = self.search([('wave_id','=',this.wave_id.id),('state','not in',['draft','cancel','done'])])
        if len(count) == 0:
            this.wave_id.done()

    @api.model
    def do_multi_validate_orders(self,picks):
        for p in picks:
            self.do_validate_orders(p)


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