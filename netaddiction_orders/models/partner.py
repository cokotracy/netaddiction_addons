# -*- coding: utf-8 -*-

from openerp import models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def write(self, values):
        """
        Consente di mantenere uno storico affidabile degli indirizzi di spedizione e fatturazione negli ordini.

        Nel caso in cui uno dei campi in *fields* venga modificato e l'indirizzo in questione è già stato
        usato in uno o più ordini, ne crea una copia disattiva.
        """
        fields = (
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

        changed_fields = set(values).intersection(fields)

        if changed_fields:
            order_model = self.env['sale.order']
            partner_model = self.env['res.partner']

            for rec in self:
                if not rec.parent_id:
                    continue

                if rec.type == 'delivery':
                    address_field = 'partner_shipping_id'
                elif rec.type == 'invoice':
                    address_field = 'partner_invoice_id'
                else:
                    continue

                orders = order_model.search([('state', '!=', 'draft'), (address_field, '=', rec.id)])

                if orders:
                    copy = partner_model.create({
                        'active': False,
                        'type': rec.type,
                        'parent_id': rec.parent_id.id,
                        'name': rec.name,
                        'vat': rec.vat,
                        'fiscalcode': rec.fiscalcode,
                        'company_address': rec.company_address,
                        'phone': rec.phone,
                        'mobile': rec.mobile,
                        'street': rec.street,
                        'street2': rec.street2,
                        'city': rec.city,
                        'zip': rec.zip,
                        'state_id': rec.state_id.id,
                        'country_id': rec.country_id.id,
                    })

                    orders.write({address_field: copy.id})

        return super(Partner, self).write(values)
