# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class CCData(models.Model):
    """docstring for ClassName"""

    _name = "netaddiction.partner.ccdata"

    _sql_constraints = [
        ('token_unique', 'unique(token, active)',
         'Esiste già una carta con questo token!'),
    ]

    active = fields.Boolean(
        string='Attivo', help="Permette di spengere la carta senza cancellarla", default=True)
    default = fields.Boolean(string="Carta di default", default=False)
    token = fields.Char(string='Token', required=True)
    last_four = fields.Char(string='Indizio', required=True)
    month = fields.Integer(string='Mese', required=True)
    year = fields.Integer(string='Anno', required=True)
    name = fields.Char(string='Titolare', required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Cliente', required=True)
    ctype = fields.Char(string='Tipo Carta', default="")
    company_id = fields.Many2one(
        'res.company', related='customer_id.company_id', store=True)

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

    @api.multi
    def unlink(self):
        for cc in self:
            if cc.active:
                open_payments = self.env['account.payment'].search(
                    [("state", "=", "draft"), ("partner_id", "=", self.customer_id.id), ("cc_token", "=", self.token)])
                if open_payments:
                    orders = ""
                    for payment in open_payments:
                        orders += " "
                        orders += payment.order_id.name
                    raise CardWithOrdersException(self.token, orders)

                # Rimuovo il token da BNL
                try:
                    self.env["netaddiction.positivity.executor"].token_delete(
                        self.customer_id.id, self.token)
                except Exception:
                    pass

                # Rimuovo il token da Stripe
                try:
                    self.env["netaddiction.stripe.executor"].token_delete(
                        self.customer_id.email, self.token)
                except Exception as e:
                    pass
        super(CCData, self).unlink()


class CCDataPartner(models.Model):
    _inherit = 'res.partner'

    ccdata_id = fields.One2many(
        'netaddiction.partner.ccdata', 'customer_id', string="Carta")


class CardWithOrdersException(Exception):
    def __init__(self, token, err_str):
        super(CardWithOrdersException, self).__init__(token)
        self.var_name = 'confirm_exception'
        self.err_str = err_str
        self.token = token

    def __str__(self):
        s = u"Questa carta non puo' essere cancellata perche' connessa a ordini non completati : %s " % (
            self.err_str)
        return s

    def __repr__(self):
        s = u"Questa carta non può essere cancellata perche' connessa a ordini non completati : %s " % (
            self.err_str)
        return s
