# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    is_default_address = fields.Boolean(string="Indirizzo di Default")
    #in realtà è il cazzo di nome dell'azienda del partner (in linguaggio normale RAGIONE SOCIALE - thanks to Bozzi)
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
                name = ''
                if s.name:
                    name += s.name
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

    @api.one
    def equals(self, partner):
        """
        Stabilisce se due partner si equivalgono confrontando tutti i campi in *fields*.
        """
        fields = 'name', 'vat', 'business_name', 'phone', 'mobile', 'street_number', 'city', 'zip_code', 'state_id', 'country_id'

        for field in fields:
            if getattr(self, field) != getattr(partner, field):
                return False

        return True

    @api.one
    def unlink(self):
        " abbiamo deciso di non far cancellare i clienti. Li archiviamo."
        self.active = False
        if self.affiliate_id:
            self.affiliate_id['active'] = False
