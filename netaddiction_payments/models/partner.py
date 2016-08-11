# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class CCData(models.Model):
    """docstring for ClassName"""

    _name = "netaddiction.partner.ccdata"

    # _sql_constraints = [
    #     ('token_unique', 'unique(token)', 'Esiste già una carta con questo token!'),
    # ]
    active = fields.Boolean(string='Attivo', help="Permette di spengere la carta senza cancellarla", default=True)
    default = fields.Boolean(string="Carta di default", default=False)
    token = fields.Char(string='Token', required=True)
    last_four = fields.Char(string='Indizio', required=True)
    month = fields.Integer(string='Mese', required=True)
    year = fields.Integer(string='Anno', required=True)
    name = fields.Char(string='Titolare', required=True)
    customer_id = fields.Many2one('res.partner', string='Cliente', required=True)
    ctype = fields.Char(string='Tipo Carta', default="")
    company_id = fields.Many2one('res.company', related='customer_id.company_id', store=True)

    @api.multi
    def name_get(self):
        res = []

        for s in self:
            res.append((s.id, ' '.join([s.name, s.last_four, s.ctype])))

        return res

    @api.constrains('default')
    @api.one
    def update_default_address(self):
        if self.default and self.customer_id:
            siblings = self.env['netaddiction.partner.ccdata'].search([
                ('customer_id', '=', self.customer_id.id),
                ('id', '!=', self.id),
                ('default', '=', True),
            ])
            siblings.write({'default': False})

    @api.one
    @api.constrains('month')
    def _check_month(self):
        if self.month < 1 or self.month > 12:
            raise ValidationError("il mese deve essere compreso tra 1 e 12")

    @api.one
    @api.constrains('year')
    def _check_year(self):
        if self.year > 2999 or self.year < 1000:
            raise ValidationError("Anno non valido")

    @api.one
    @api.constrains('token')
    def _check_token(self):
        print self.token
        print self.id
        a = self.env['netaddiction.partner.ccdata'].search([('token', '=', self.token), ('active', '=', True), ("id", "!=", self.id)])
        print a
        if self.env['netaddiction.partner.ccdata'].search([('token', '=', self.token), ('active', '=', True), ("id", "!=", self.id)]):
            raise ValidationError("il mese deve essere compreso tra 1 e 12")

    @api.multi
    def unlink(self):
        for cc in self:
            self.env["netaddiction.positivity.executor"].token_delete(self.customer_id.id, self.token)
            self.active = False


class CCDataPartner(models.Model):
    _inherit = 'res.partner'

    ccdata_id = fields.One2many('netaddiction.partner.ccdata', 'customer_id', string="Carta")
