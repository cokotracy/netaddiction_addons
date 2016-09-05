# -*- coding: utf-8 -*-

from openerp import models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def write(self, values):
        picking_id = self.env.ref('stock.picking_type_in').id
        if 'product_uom_qty' in values:
            for move in self:
                # qua devo controllare che sia una spedizione in entrata
                if move.picking_id.picking_type_id.id == picking_id:
                    if int(values['product_uom_qty']) < int(move.product_uom_qty):
                        if move.purchase_line_id:
                            move.purchase_line_id.product_qty = values['product_uom_qty']
                            move.linked_move_operation_ids.operation_id.product_qty = values['product_uom_qty']

        return super(StockMove, self).write(values)

    @api.multi
    def delete_backorder(self):
        """
        mette in bozza e cancella la move solo se è una spedizione in entrata,
        cancella anche tutte le spedizioni e pack operation corrispondenti e purchase order line
        """
        picking_id = self.env.ref('stock.picking_type_in').id
        for move in self:
            # qua devo controllare che sia una spedizione in entrata
            if move.picking_id.picking_type_id.id == picking_id:
                move.action_cancel()
                move.write({'state': 'draft'})
                self.env.cr.commit()
                if move.purchase_line_id:
                    move.purchase_line_id.unlink()
                if move.linked_move_operation_ids:
                    move.linked_move_operation_ids.operation_id.unlink()
                    move.linked_move_operation_ids.unlink()
                origin = move.origin
                move.unlink()

                order = self.env['purchase.order'].search([('name', '=', origin)])
                if len(order.order_line) == 0:
                    order.state = 'cancel'
                    order.unlink()
        return True
