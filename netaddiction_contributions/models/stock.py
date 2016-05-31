# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class StockQuants(models.Model):
    _inherit = "stock.quant"

    def _get_inventory_value(self, cr, uid, quant, context=None):
        value = super(StockQuants,self)._get_inventory_value(cr, uid, quant, context=None)
        return quant._get_new_inventory_value(value)[0]

    @api.one 
    def _get_new_inventory_value(self, value):
        """
        Sottraggo il valore di rivalutazione, se presente
        """
        m_ids = []
        for history in self.history_ids:
            if len(history.picking_id.purchase_id) == 1:
                m_ids.append(history.id)
        #prendo le quants prima di self che hanno l'entrata in magazzino (acquisto da fornitore) giusto
        quants = self.env['stock.quant'].search([('history_ids','in',m_ids),('id','<',self.id)])
        old_qty = 0
        for quant in quants:
            old_qty += quant.qty
        #old_qty è la quantità prima di self
        move_contribution = self.env['netaddiction.move.contribution'].search([('move_ids','in',m_ids)])
        c_value = 0.00
        no_revaluation_qty = 0
        for history in self.history_ids:
            if len(history.picking_id.purchase_id) == 1:
                for m in move_contribution:
                    #quantità in cui mi trovo in questo momento
                    current_qty = old_qty + self.qty
                    #la quantità che non deve essere rivalutata perchè fuori dai limiti imposti
                    no_revaluation_qty += (history.product_uom_qty - m.qty)
                    
                    to_revaluation = current_qty - no_revaluation_qty

                    if to_revaluation > 0 and to_revaluation <= self.qty:
                        c_value += m.unit_value * to_revaluation
                    elif to_revaluation > 0 and to_revaluation > self.qty:
                        c_value += m.unit_value * self.qty
   
        value -= c_value
        return value