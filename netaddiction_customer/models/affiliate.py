# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Affiliate(models.Model):
    _name = "netaddiction.partner.affiliate"
    _inherit = 'res.partner'
    active = fields.Boolean(string="Attivo")
    control_code = fields.Integer(string = "Codice di controllo")
    homepage = fields.Char(string = "Sito")
    commission_percent = fields.Float(string="Percentuale commissioni")
    

