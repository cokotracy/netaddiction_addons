# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):

    _inherit = 'res.partner'

    FIELDS_FREEZE = (
        'name',
        'vat',
        'fiscalcode',
        'company_address',
        'phone',
        'mobile',
        'street',
        'street2',
        'city',
        'zip',
        'state_id',
        'country_id',
    )

    @api.multi
    def write(self, values):
        if self.env.context.get('skip_reduplicate_partner', False):
            return super().write(values)
        changed_fields = set(values).intersection(self.FIELDS_FREEZE)
        if changed_fields:
            partners_on_orders = []
            order_model = self.env['sale.order']
            for partner in self:
                orders = order_model.search([
                    '|',
                    ('partner_shipping_id', '=', partner.id),
                    ('partner_invoice_id', '=', partner.id),
                    ('state', '!=', 'draft'),
                    ])
                if orders:
                    partners_on_orders.append(partner)
            if partners_on_orders:
                raise UserError(_(
                    'Impossibile to change values for fields "{fields}" '
                    'for partners "{partners}" because of used in orders.\n'
                    'Duplicate them/it and set new values').format(
                        fields=','.join(changed_fields),
                        partners=','.join(
                            [p.name for p in partners_on_orders]),
                    ))
        return super().write(values)
