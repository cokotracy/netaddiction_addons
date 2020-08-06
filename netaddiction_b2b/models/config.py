# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    pricelist_csv_ftp_host = fields.Char(
        related='company_id.pricelist_csv_ftp_host',
        string='Host',
        readonly=False
    )

    pricelist_csv_ftp_user = fields.Char(
        related='company_id.pricelist_csv_ftp_user',
        string='User',
        readonly=False
    )

    pricelist_csv_ftp_password = fields.Char(
        related='company_id.pricelist_csv_ftp_password',
        string='Password',
        readonly=False
    )

    public_pricelist_id = fields.Many2one(
        'product.pricelist',
        related='company_id.public_pricelist_id',
        string='Public Pricelist',
        readonly=False
    )
