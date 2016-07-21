# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp import exceptions
import openerp.addons.decimal_precision as dp
import datetime

class ProductMargin(models.Model):
    _inherit="sale.order.line"

    #margin_new = fields.Float(string="Margine Prodotto", compute="_calculate_product_margin", store = False, digits_compute= dp.get_precision('Product Price'))

    #purchase_price_real = fields.Float(string="Costo", compute = "_calculate_purchase_price_real", digits_compute= dp.get_precision('Product Price'))
    
    margin_new = fields.Float(string="Margine Prodotto",digits_compute= dp.get_precision('Product Price'))
    purchase_price_real = fields.Float(string="Costo",digits_compute= dp.get_precision('Product Price'))

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
        count = 0
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
        quant = self.sudo().env['stock.quant'].search(['|',('reservation_id','=',this_move.id),('history_ids','in',[this_move.id])])
        #se ne ho più di uno significa che viene preso da più fornitori o da due righi di prezzo diversi
        #faccio la media per evitare casini
        num = 0
        price = 0
        for q in quant:
            num += q.qty
            inv_value = self.product_id.supplier_taxes_id.compute_all(q.inventory_value)['total_excluded']
            price += q.inventory_value

        if num == 0:
            self.purchase_price_real = 0.00
        else:
            self.purchase_price_real = price / num

    @api.one 
    def _calculate_product_margin(self):
        #vedo se l'ordine che contiene questa riga ha associato qualche contributo sul venduto
        contribution = self.env['netaddiction.order.contribution'].search([('order_id','=',self.order_id.id),
            ('contribution_id.product_id','=',self.product_id.id)])
        cont_value = 0
        ids = []
        if len(contribution) > 0:
            for cont in contribution:
                #TASSE: diamo per scontato che i contributi sono tasse escluse
                cont_value += cont.unit_value * cont.qty
                ids.append(cont.contribution_id.id)
        #a questo punto verifico eventuali nuovi contributi non calcolati ancora
        other_contribution = self.env['netaddiction.contribution'].search([('contribution_type','=','valuexship'),
            ('product_id','=',self.product_id.id),('id','not in',ids),('date_start','<=',self.order_id.date_order),
            ('date_finish','>=',self.order_id.date_order)])
        #devo recuperare le moves se ho altri contributi
        if len(other_contribution) > 0:
            pick_ids = []
            group_ids = []
            for pick in self.order_id.picking_ids:
                pick_ids.append(pick.id)
                if pick.group_id.id is not False:
                    group_ids.append(pick.group_id.id)

            moves = self.env['stock.move'].search([('picking_id','in',pick_ids),('product_id','=',self.product_id.id),
                ('product_uom_qty','=',self.product_qty),('group_id','in',group_ids)])
            move_ids = []
            for move in moves:
                move_ids.append(move.id)

            quants = self.env['stock.quant'].search(['|',('reservation_id','in',move_ids),('history_ids','in',move_ids)])
            #per ogni quant controllo che ci sia l'acquisto e faccio i conteggi
            reverse = self.qty_reverse
            for quant in quants:
                for history in quant.history_ids:
                    if len(history.picking_id.purchase_id) == 1:
                        for oc in other_contribution:
                            if history.picking_id.partner_id.id == oc.partner_id.id:
                                max_qta = oc.qty - oc.confirmed_qty
                                #se non ci sono quantità rese vai avanti
                                #in teoria il reverse ha creato una quant a parte quindi dovrebbe andare bene sempre
                                if reverse <= 0:
                                    if max_qta > quant.qty:
                                        qty_add = quant.qty
                                    else:
                                        qty_add = max_qta

                                    attr = {
                                        'order_id' : self.order_id.id,
                                        'contribution_id' : oc.id,
                                        'qty' : qty_add,
                                        'unit_value' : oc.value
                                    }
                                    self.sudo().env['netaddiction.order.contribution'].create(attr)
                                    self.env.cr.commit()
                                    cont_value += oc.value * qty_add
                                #decrementi le quantità rese
                                reverse -= quant.qty
        if self.purchase_price_real != 0:
            #MOD TASSE
            #qua prendo tutti i prezzi indipendentemente dall'iva
            price_unit = self.product_id.taxes_id.compute_all(self.price_unit)['total_excluded']
            self.margin_new = (price_unit * (self.product_qty-self.qty_reverse)) - (self.purchase_price_real * (self.product_qty-self.qty_reverse)) + cont_value
        else:
            self.margin_new = 0


class OrderMargin(models.Model):
    _inherit="sale.order"

    #margin_new = fields.Float(string="Margine", compute="_calculate_order_margin", store = True, digits_compute= dp.get_precision('Product Price'),
    #    help="Il margine è calcolato solo sui prodotti (escluse le spese di spedizione) ed è scorporato dell'iva") 

    margin_new = fields.Float(string="Margine Ordine", digits_compute= dp.get_precision('Product Price'))
    
    is_complete_margin = fields.Boolean(string="Margina calcolato", default = False)
    #@api.one
    #def _calculate_order_margin(self):
    #    margin_new = 0
    #    for line in self.order_line:
    #        margin_new += line.margin_new
            
    #    self.margin_new = margin_new