from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_priority = fields.Selection(
        [('0', '0'),
         ('1', '1'),
         ('2', '2'),
         ('3', '3'),
         ('4', '4'),
         ('5', '5'),
         ('6', '6'),
         ('7', '7'),
         ('8', '8'),
         ('9', '9'),
         ('10', '10')],
        default='9',
        help="Priorità fornitore: più alta è la priorità più verrà preso in"
             " considerazine per gli ordini e le disponibilità prodotto",
        string="Priorità Fornitore",
    )

    supplier_delivery_time = fields.Integer(
        default=1,
        string="Tempo di consegna del fornitore",
    )
