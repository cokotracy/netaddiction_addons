# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Gift(models.Model):
    _name = "netaddiction.gift"
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente")
    type_id = fields.Many2one(
        comodel_name='netaddiction.gift.type',
        string="Type")
    value = fields.Float(string="Valore")
    reason = fields.Selection([('r','Rimborso'),('a','Altro')], string='Motivazione', default='r')

    @api.one
    @api.constrains('value')
    def _check_value(self):
        if self.value < 0.0:
            self.value = 0.0
            raise ValidationError("Il valore del gift deve essere maggiore uguale a zero")

class GiftCustomer(models.Model):
    _inherit = 'res.partner'
    gift_ids = fields.One2many(
        comodel_name='netaddiction.gift',
        inverse_name='id',
        string='Gift')
    total_gift = fields.Float(compute='_compute_total_gift')



    @api.depends('gift_ids')
    def _compute_total_gift(self):
        for record in self:
            for gift in gift_ids:
                record.total += gift.value

class GiftType(models.Model):
    _name = "netaddiction.gift.type"
    reason = fields.Char('Motivazione')
    priority = fields.Selection([(0,'Molto Alta'),(1,'Alta'),(2,'Media'),(3,'Bassa'),(4,'Molto Bassa')], string='Priorità', default=2)
    gift_ids = fields.One2many(
        comodel_name='netaddiction.gift',
        inverse_name='id',
        string='Gift')

