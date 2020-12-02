from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_id = fields.Many2one(
        'account.payment',
        string='Pagamento',
    )
