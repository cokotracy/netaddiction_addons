# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Partners(models.Model):
    _inherit = 'res.partner'

    is_default_delivery_address = fields.Boolean(string="Indirizzo di Default")

    # TODO: quando salva e is_default_delivery_address is true allora deve mettere a false
    # tutti gli altri indirizzi.
    # in pratica per tutti gli indirizzi deve esserci solo un indirizzo di default
