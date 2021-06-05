from odoo import fields, models


class Orders(models.Model):
    _inherit = 'sale.order.line'

    qty_reverse = fields.Integer(
        compute='_get_qty_reverse',
        string="Reso",
    )

    stock_line_ids = fields.Many2many(
        'stock.move.line',
        string="Linee spedizione collegate",
    )

    def _get_qty_reverse(self):
        """
        Conta la quantità resa per quel riga ordine
        """
        for line in self:
            reverse = 0
            for pick in line.order_id.get_reverse_pickings():
                for line in pick.move_line_ids:
                    if line.product_id.id == self.product_id.id:
                        reverse += line.qty_done
            line.qty_reverse = reverse
