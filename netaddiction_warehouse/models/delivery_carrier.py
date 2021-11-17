# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = 'delivery.carrier'

    time_to_shipping = fields.Integer(
        default=1,
        string="Tempo di Consegna",
    )

    base_tracking_url = fields.Char(string="URL base per il tracciamento")

    manifest_ftp_url = fields.Char()

    manifest_ftp_user = fields.Char()

    manifest_ftp_password = fields.Char()

    manifest_ftp_path = fields.Char()

    cash_on_delivery_payment_method_id = fields.Many2one(
        'payment.acquirer',
        string='Sistema di Pagamento Contrassegno',
    )

    def get_tracking_url(self, code=""):
        if not self.base_tracking_url:
            return "#"
        return self.base_tracking_url % code
