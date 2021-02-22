# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Get all the pricelists created by the user in the old Odoo version.
        # To recognize manual ones, we exclude those with metadata
        # (created by the base modules)
        base_pricelist_data = env['ir.model.data'].search([
            ('model', '=', 'product.pricelist'), ])
        base_pricelists = env['product.pricelist'].browse(
            base_pricelist_data.mapped('res_id'))
        to_delete_pricelists = env['product.pricelist'].search(
            [('id', 'not in', base_pricelists.ids)]
        )
        # Pricelists can't be deleted.
        # So, we delete items and disable headers.
        to_delete_pricelists.mapped('item_ids').unlink()
        to_delete_pricelists.active = False
