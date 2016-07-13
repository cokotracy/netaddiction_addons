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
                res.append((s.id, s.name + ', ' + s.city + ' ' + s.street + ' ' + s.street2))
            else:
                res.append((s.id, s.name))

        return res

    @api.constrains('is_default_address')
    @api.one
    def update_default_address(self):
        if self.is_default_address and self.parent_id:
            siblings = self.parent_id.child_ids.search([('id', '!=', self.id), ('type', '=', self.type)])
            siblings.write({'is_default_address': False})

    @api.one
    def unlink(self):
        " abbiamo deciso di non far cancellare i clienti. Li archiviamo."
        self.active = False
        if self.affiliate_id:
            self.affiliate_id['active'] = False
