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

    manifest_ftp_url = fields.Char()

    manifest_ftp_user = fields.Char()

    manifest_ftp_password = fields.Char()

    manifest_ftp_path = fields.Char()
