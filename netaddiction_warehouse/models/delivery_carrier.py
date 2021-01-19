from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    time_to_shipping = fields.Integer(
        default=1,
        string="Tempo di Consegna",
    )
