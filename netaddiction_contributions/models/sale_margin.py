# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp import exceptions
import datetime

class ProductMargin(models.Model):
    _inherit="sale.order.line"

    margin = fields.Float(string="Margine Prodotto", compute="_calculate_product_margin", store = False)

    purchase_price_real = fields.Float(string="Costo New", compute = "_calculate_purchase_price_real")

    @api.one 
    def _calculate_purchase_price_real(self):
        pick_ids = []
        group_ids = []
        for pick in self.order_id.picking_ids:
            pick_ids.append(pick.id)
            if pick.group_id.id is not False:
                group_ids.append(pick.group_id.id)

        moves = self.env['stock.move'].search([('picking_id','in',pick_ids),('product_id','=',self.product_id.id),
            ('product_uom_qty','=',self.product_qty),('group_id','in',group_ids)])

        if len(moves) == 0:
            self.purchase_price_real = 0.0
            return True

        all_moves = []
        for move in moves:
            all_moves.append(move)
        
        #diamo per scontato che id di linea ordine bassi si accoppiano con id di move bassi, alti con alti e così via
        #se per un assurdo motivo così non è, ce ne fottiamo allegramente
        this_move = all_moves[0]

        #detto questo vado a cercare se ci sono altre righe ordine con lo stesso prodotto e la stessa quantità
        if len(moves)>1:
            lines = self.search([('product_id','=',self.product_id.id),('order_id','=',self.order_id.id)])
            count = 0
            for line in lines:
                if line.id == self.id:
                    break
                count += 1
        
            this_move = all_moves[count]

        #a questo punto devo trovare le quants
        #una quant con reservation_id = alla move è una quant riservata
        #se non c'è la quant riservata allora la cerco in history_ids
        quant = self.env['stock.quant'].search(['|',('reservation_id','=',this_move.id),('history_ids','in',[this_move.id])])
        #se ne ho più di uno è come sopra id bassi => quant id bassi etc (alla fin fine quando partono tutti si sistema a dovere)
        print quant
            
        self.purchase_price_real = 0.0

    @api.one 
    def _calculate_product_margin(self):
               

        return 0.0


class OrderMargin(models.Model):
    _inherit="sale.order"

    margin = fields.Float(string="Margine", compute="_calculate_order_margin", store = False) 

    @api.one
    def _calculate_order_margin(self):
        margin = 0
        for line in self.order_line:
            margin += line.margin

        self.margin = margin