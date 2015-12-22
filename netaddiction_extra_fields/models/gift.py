# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Gift(models.Model):
    _name = "netaddiction.gift"
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente", required=True)
    type_id = fields.Many2one(
        comodel_name='netaddiction.gift.type',
        string="Type", required = True)
    value = fields.Float(string="Valore")
    #reason = fields.Selection([('r','Rimborso'),('a','Altro')], string='Motivazione', default='r')

    @api.one
    @api.constrains('value')
    def _check_value(self):
        print "VALUE"
        print self.value
        print self.type_id.reason
        if self.value < 0.0:
            self.value = 0.0
            raise ValidationError("Il valore del gift deve essere maggiore uguale a zero")

    @api.one
    @api.constrains('partner_id')
    def _check_partner_id(self):

        if self.partner_id is None or self.partner_id.type != 'contact' :
            raise ValidationError("Il gift può essere assegnato solo a clienti")

   

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
    _rec_name = 'reason'
    reason = fields.Char('Motivazione')
    priority = fields.Selection([(0,'Molto Alta'),(1,'Alta'),(2,'Media'),(3,'Bassa'),(4,'Molto Bassa')], string='Priorità', default=2)
    gift_ids = fields.One2many(
        comodel_name='netaddiction.gift',
        inverse_name='id',
        string='Gift')

