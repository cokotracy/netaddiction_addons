# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class CCData(models.Model):
    """docstring for ClassName"""

    _name = "netaddiction.partner.ccdata"


    default = fields.Boolean(string="Carta di default", default =False)
    token = fields.Char(string='Token', required=True)
    last_four = fields.Char(string='Indizio', required=True)
    month = fields.Integer(string='Mese', required = True)
    year =  fields.Integer(string='Anno', required = True)
    name = fields.Char(string='Titolare', required=True)
    customer_id = fields.Many2one('res.partner', string='Cliente',required=True)
    ctype = fields.Char(string='Tipo Carta')

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



class CCDataPartner(models.Model):
    _inherit = 'res.partner'

    ccdata_id = fields.One2many('netaddiction.partner.ccdata','customer_id', string="Carta")


