# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    is_default_address = fields.Boolean(string="Indirizzo di Default")
    # in realtà è il cazzo di nome dell'azienda del partner (in linguaggio normale RAGIONE SOCIALE - thanks to Bozzi)
    company_address = fields.Char(string="Ragione Sociale")
    rating = fields.Selection([('0', 'Negativo'), ('1', 'Medio'), ('2', 'Positivo')], string='Rating', default="2")
    email_rating = fields.Selection([('A+', 'A+'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('', 'Non valutato')], string='Email Rating', default='')
    birthdate = fields.Date(string="Data di nascita")

    @api.multi
    def name_get(self):
        res = []

        for s in self:
            if len(s.parent_id) > 0 and s.customer:
                name = ''
                if s.name:
                    name += s.name + ', '
                if s.city:
                    name += s.city + ' '
                if s.street:
                    name += s.street + ' '
                if s.street2:
                    name += s.street2 + ' '

                res.append((s.id, name))
            else:
                name = str(s.id)
                if s.name:
                    name += ' - ' + s.name
                res.append((s.id, name))

        return res

    @api.constrains('is_default_address')
    @api.one
    def update_default_address(self):
        if self.is_default_address and self.parent_id:
            siblings = self.env['res.partner'].search([
                ('parent_id', '=', self.parent_id.id),
                ('id', '!=', self.id),
                ('type', '=', self.type),
                ('is_default_address', '=', True),
            ])
            siblings.write({'is_default_address': False})

    def equals(self, partner):
        """
        Stabilisce se due partner si equivalgono confrontando tutti i campi in *fields*.
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

        for field in fields:
            value = partner.get(field) if isinstance(partner, dict) else getattr(partner, field)

            if (getattr(self, field) or False) != (value or False):
                return False

        return True

    def get_as(self, typology='invoice'):
        """
        Restituisce un indirizzo equivalente ma di tipo *typology*.
        """
        invoice_addresses = self.env['res.partner'].search([
            ('parent_id', '=', self.parent_id.id),
            ('type', '=', typology),
        ])

        for invoice_address in invoice_addresses:
            if self.equals(invoice_address):
                return invoice_address

        return self.env['res.partner'].create({
            'type': typology,
            'parent_id': self.parent_id.id,
            'name': self.name,
            'vat': self.vat,
            'fiscalcode': self.fiscalcode,
            'company_address': self.company_address,
            'phone': self.phone,
            'mobile': self.mobile,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'zip': self.zip,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
        })

    @api.one
    def unlink(self):
        " abbiamo deciso di non far cancellare i clienti. Li archiviamo."
        self.active = False
        if self.affiliate_id:
            self.affiliate_id['active'] = False
