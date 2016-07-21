# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    is_default_address = fields.Boolean(string="Indirizzo di Default")
    company_address = fields.Char(string="Azienda")
    rating = fields.Selection([('0', 'Negativo'), ('1', 'Medio'), ('2', 'Positivo')], string='Rating', default="2")
    email_rating = fields.Selection([('A+', 'A+'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('', 'Non valutato')], string='Email Rating', default='')
    birthdate = fields.Date(string="Data di nascita")

    @api.multi
    def name_get(self):
        res = []

        for s in self:
            if len(s.parent_id) > 0 and s.customer:
                name = ''
                if s.name is not False:
                   name += s.name + ', '
                if s.city is not False:
                   name += s.city + ' '
                if s.street is not False:
                   name += s.street + ' '
                if s.street2 is not False:
                   name += s.street2 + ' '

                res.append((s.id, name))
            else:
                name = ''
                if s.name is not False:
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
    def unlink(self):
        " abbiamo deciso di non far cancellare i clienti. Li archiviamo."
        self.active = False
        if self.affiliate_id:
            self.affiliate_id['active'] = False
