# Copyright 2021 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # These two fields have been reimplemented because Odoo 13 doesn't use
    # them anymore by default. They should not interfere with the standard
    # Odoo business logic

    customer = fields.Boolean(
        string='Is a Customer',
        default=True,
        help="Check this box if this contact is a customer. It can be selected"
             " in sales orders.")

    supplier = fields.Boolean(
        string='Is a Vendor',
        help="Check this box if this contact is a vendor. It can be selected"
             " in purchase orders."
        )