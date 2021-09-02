# FIXME This file has been disabled as we likely don't want to have this feature
# and want to use the standard Odoo features instead. This file might be
# completely removed later on.

from odoo import fields, models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    deleted_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Ordine da rettificare',
    )

    def assign_supplier(self):
        self.ensure_one()
        wh_stock = self.env.ref('stock.stock_location_stock')
        pick_type_in = self.env.ref('stock.picking_type_in')
        # prendo i prodotti del carico
        for move in self.move_ids:
            # effettuo il collegamento col fornitore solo se lo spostamento è verso il magazzino
            if move.location_dest_id == wh_stock:
                for quant in move.quant_ids:
                    sup = quant.get_supplier()
                    # se per qualche assurdo motivo il fornitore già c'è meglio così
                    if not sup and self.deleted_order_id:
                        for pick_quant in self.deleted_order_id.mapped(
                            'picking_ids.move_lines.quant_ids'
                        ):
                            if pick_quant.product_id.id == move.product_id.id:
                                # FIXME: history_ids non esiste più
                                # for history in pick_quant.history_ids:
                                #     quant.history_ids += history
                                pass
                    # se non ho l'ordine, trovo per quel prodotto, le quants
                    # con in_date (data d'ingresso) minore della sua data
                    # nell'history di queste quant controllo quante ne mancano
                    # e semmai gliele assegno
                    if not sup and not self.deleted_order_id:
                        old_moves = self.env['stock.move'].search(
                            [('product_id.id', '=', quant.product_id.id),
                             ('date', '<', quant.in_date),
                             ('location_dest_id.id', '=', wh_stock),
                             ('picking_type_id', '=', pick_type_in.id)],
                            order='date desc'
                        )
                        if old_moves:
                            # FIXME: history_ids non esiste più
                            # quant.history_ids = [(4, old_moves[0].id, False)]
                            pass
        return True

    def _action_done(self):
        res = super()._action_done()
        for inv in self:
            inv.sudo().assign_supplier()
        return res
