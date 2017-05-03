# -*- coding: utf-8 -*-
from openerp import models, fields, api

class GrouponPickup(models.Model):
    _name = 'groupon.pickup.wave'

    name = fields.Char(string="Nome")
    order_ids = fields.One2many(comodel_name='netaddiction.groupon.sale.order', string='Ordini', inverse_name="wave_id")
    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('done', 'Completato'),
    ], string='Stato', readonly=True, default="draft")
    date_close = fields.Datetime(string="Data Chiusura")

    @api.model
    def create_wave(self):
        orders = self.env['netaddiction.groupon.sale.order'].search([('state', '=', 'draft'), ('picking_ids', '!=', False), ('wave_id', '=', False)])

        if len(orders) > 0:
            attr = {
                'order_ids': [(6, False, orders.mapped('id'))],
            }
            wave = self.create(attr)
            wave.name = 'Lista Groupon %s' % (wave.id)

            return 'ok'
        else:
            return 'Non ci sono ordini da pickuppare.'
