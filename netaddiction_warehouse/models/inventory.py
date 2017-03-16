# -*- coding: utf-8 -*-
from openerp.exceptions import Warning
from openerp import models, fields, api

class StockInventory(models.Model):

    _inherit = "stock.inventory"

    deleted_order_id = fields.Many2one(string='Ordine da rettificare', comodel_name='sale.order')

    @api.one
    def assign_supplier(self):
        wh_stock = self.env.ref('stock.stock_location_stock').id
        # sup_stock = self.env.ref('stock.stock_location_suppliers').id
        # cus_stock = self.env.ref('stock.stock_location_customers').id
        # inventory_loss = self.env.ref('stock.location_inventory').id
        # prendo i prodotti del carico
        for move in self.move_ids:
            # effettuo il collegamento col fornitore solo se lo spostamento è verso il magazzino
            if move.location_dest_id.id == wh_stock:
                for quant in move.quant_ids:
                    sup = quant.get_supplier()
                    # se per qualche assurdo motivo il fornitore già c'è meglio così
                    if not sup and self.deleted_order_id:
                        for pick in self.deleted_order_id.picking_ids:
                            for pick_move in pick.move_lines:
                                for pick_quant in pick_move.quant_ids:
                                    if pick_quant.product_id.id == move.product_id.id:
                                        for history in pick_quant.history_ids:
                                            quant.history_ids = [(4, history.id, False)]
                    # se non ho l'ordine, trovo per quel prodotto, le quants con in_date (data d'ingresso) minore della sua data
                    # nell'hisotry di queste quant controllo quante ne mancano e semmai gliele assegno
                    if not sup and not self.deleted_order_id:
                        old_moves = self.env['stock.move'].search([('product_id.id', '=', quant.product_id.id), ('date', '<', quant.in_date), ('location_dest_id.id', '=', wh_stock), ('picking_type_id', '=', 1)], order="date desc")
                        if old_moves:
                            quant.history_ids = [(4, old_moves[0].id, False)]
        return True

    @api.multi
    def action_done(self, value):
        super(StockInventory, self).action_done(context=value)

        for inv in self:
            inv.sudo().assign_supplier()

        return True
