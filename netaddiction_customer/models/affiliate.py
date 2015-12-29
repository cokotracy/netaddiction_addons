# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Affiliate(models.Model):
    _name = "netaddiction.partner.affiliate"

    active = fields.Boolean(string="Attivo")
    control_code = fields.Integer(string = "Codice di controllo")
    homepage = fields.Char(string = "Sito")
    commission_percent = fields.Float(string="Percentuale commissioni")
    date_account_created = fields.Datetime(string="Data creazione")
    cookie_duration = fields.Integer(string = "Durata Cookie")
    exclude_from_cron = fields.Boolean(string="Escluso dal cron")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente", required=True)


    @api.one
    @api.constrains('commission_percent')
    def _check_value(self):
        if self.commission_percent < 0.0 or self.commission_percent > 100.0:
            raise ValidationError("Percentuale commissioni deve essere compreso tra 0 e 100")

class GiftCustomer(models.Model):
    _inherit = 'res.partner'
    affiliate_id = fields.Many2one(
        comodel_name='netaddiction.partner.affiliate',
        string='Dati Affiliato' )
    total_gift = fields.Float(compute='_compute_total_gift')



    @api.depends('gift_ids')
    def _compute_total_gift(self):
        for record in self:
            for gift in gift_ids:
                record.total += gift.value