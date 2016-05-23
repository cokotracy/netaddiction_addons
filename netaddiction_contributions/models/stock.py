# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class StockQuants(models.Model):
    _inherit = "stock.quant"

    def _get_inventory_value(self, cr, uid, quant, context=None):
        value = super(StockQuants,self)._get_inventory_value(cr, uid, quant, context=None)
        return quant._get_new_inventory_value(value)

    @api.multi 
    def _get_new_inventory_value(self, value):
        """
        Sottraggo il valore di rivalutazione, se presente
        """
        self.ensure_one()
        c_value = 0
        for history in self.history_ids:
            if len(history.picking_id.purchase_id) == 1:
                move_contribution = self.env['netaddiction.move.contribution'].search([('move_ids','in',history.id)])
                if len(move_contribution) > 0:
                    for m in move_contribution:
                        if self.qty < m.qty:
                            c_value += self.qty * m.unit_value
                        else:
                            c_value += m.qty * m.unit_value
        value -= c_value
        return value