# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
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

    rating = fields.Selection(
        [('0', 'Negativo'), ('1', 'Medio'), ('2', 'Positivo')],
        string='Rating',
        default="2"
    )

    def write(self, values):
        if self.env.context.get('skip_reduplicate_partner', False):
            return super().write(values)
        # TODO: FIXME The best way to execute this kind of check is to keep
        # values before and after the write and raise an error
        # only if values are changed.
        # In a write is possibile to send the some data again to the record
        # but this not means that them are changed.
        # Delete empty value from values to check
        values_to_check = values.copy()
        for val_key, val_value in values.items():
            if not val_value:
                del values_to_check[val_key]
        changed_fields = set(values_to_check).intersection(self.FIELDS_FREEZE)
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

    def generate_key(self):
        res = super().generate_key()
        # If partner hasn't a program, add it
        if not self.affiliate_program_id:
            affiliate_program = self.env['affiliate.program'].search(
                [], limit=1)
            self.affiliate_program_id = affiliate_program.id
        return res
