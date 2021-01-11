from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        """
        COMPLETE OVERRIDE OF STANDARD METHOD
        Please see the comments in the code
        """

        # Override 1: do not raise errors even if moves are in 'done' state
        # if any(move.state == 'done' and not move.scrapped for move in self):
        #     raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
        moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
        # self cannot contain moves that are either cancelled or done, therefore we can safely
        # unlink all associated move_line_ids
        moves_to_cancel._do_unreserve()

        for move in moves_to_cancel:
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            if move.propagate_cancel:
                # Override 2: cancel every sibling move
                # if all(state == 'cancel' for state in siblings_states):
                #     move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
                move.move_dest_ids._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})

        # NB: we will safely call the ``super`` now to allow other methods
        # to act correctly
        return super()._action_cancel()

    ##########
    # CARICO #
    ##########

    @api.model
    def complete_operation(self, ids, qta):
        """
        completa le righe dell'ordine di consegna in entrata per il carico
        in base alla qta passata per il prodotto presente nelle righe (ids)
        """
        operations = self.search([('id', 'in', ids)])
        to_remove = qta
        for op in operations:
            residual = int(op.product_uom_qty) - int(op.quantity_done)
            if residual >= to_remove:
                op.quantity_done += to_remove
                break
            if residual < to_remove:
                op.quantity_done += residual
                to_remove -= residual
