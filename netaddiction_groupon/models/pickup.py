# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
import datetime

class GrouponPickup(models.Model):
    _name = 'groupon.pickup.wave'

    name = fields.Char(string="Nome")
    picking_ids = fields.Many2many('stock.picking', string='Spedizioni')
    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('done', 'Completato'),
    ], string='Stato', readonly=True, default="draft")
    date_close = fields.Datetime(string="Data Chiusura")

    @api.model
    def create_wave(self):
        return 'ciao'