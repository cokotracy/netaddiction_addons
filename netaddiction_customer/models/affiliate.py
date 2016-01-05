# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Affiliate(models.Model):
    _name = "netaddiction.partner.affiliate"
    _rec_name = 'control_code'

    active = fields.Boolean(string="Attivo", default=True)
    control_code = fields.Integer(string = "Codice di controllo")
    homepage = fields.Char(string = "Sito")
    commission_percent = fields.Float(string="Percentuale commissioni")
    date_account_created = fields.Datetime(string="Data creazione")
    cookie_duration = fields.Integer(string = "Durata Cookie")
    exclude_from_cron = fields.Boolean(string="Escluso dal cron")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente", required=True)


    @api.model
    def create(self,values):
        myself = super(Affiliate, self).create(values)
        self.env['res.partner'].search([('id','=',values['partner_id'])])[0]['affiliate_id'] = myself
        return myself

    @api.one
    @api.constrains('commission_percent')
    def _check_value(self):
        if self.commission_percent < 0.0 or self.commission_percent > 100.0:
            raise ValidationError("Percentuale commissioni deve essere compreso tra 0 e 100")

class AffiliateCustomer(models.Model):
    _inherit = 'res.partner'
    affiliate_id = fields.Many2one(
        comodel_name='netaddiction.partner.affiliate',
        string='Dati Affiliato')



    @api.constrains('affiliate_id')
    def _constrains_set_a_id(self):
        if len(self.affiliate_id) > 1:
            raise openerp.exceptions.ValidationError('Questo cliente è già un affiliato!')

    @api.multi
    def new_customer_affiliate(self):

        view_id = self.env.ref('netaddiction_customer.netaddiction_sales_affiliate_form').id
        return {
            'name':'Nuova Affiliato',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'netaddiction.partner.affiliate',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'context':{
                'default_partner_id' : self.id,
                 },
        }
   