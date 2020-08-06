# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    pricelist_csv_ftp_host = fields.Char(
        string='Host'
    )

    pricelist_csv_ftp_password = fields.Char(
        string='Password'
    )

    pricelist_csv_ftp_user = fields.Char(
        string='User'
    )

    public_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Public Pricelist'
    )
