# TODO removed from __init__
from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    ##########
    # CARICO #
    ##########

    # TODO moved inside model stock.move
    # @api.model
    # def complete_operation(self, ids, qta):
    #     """
    #     completa le righe dell'ordine di consegna in entrata per il carico
    #     in base alla qta passata per il prodotto presente nelle righe (ids)
    #     """
    #     operations = self.search([('id', 'in', ids)])
    #     to_remove = qta
    #     for op in operations:
    #         residual = int(op.product_qty) - int(op.qty_done)
    #         if residual >= to_remove:
    #             op.qty_done += to_remove
    #             break
    #         if residual < to_remove:
    #             op.qty_done += residual
    #             to_remove -= residual
