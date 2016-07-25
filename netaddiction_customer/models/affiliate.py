# -*- coding: utf-8 -*-
import openerp
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from hashids import Hashids
from datetime import datetime, timedelta


class Affiliate(models.Model):
    """ATTENZIONE: se l'affiliato non ha commissioni viene usato self.commission_percent su ogni prodotto
    """
    _name = "netaddiction.partner.affiliate"
    _rec_name = 'control_code'

    active = fields.Boolean(string="Attivo", default=True)
    control_code = fields.Integer(string="Codice di controllo")
    homepage = fields.Char(string="Sito")
    commission_percent = fields.Float(string="Percentuale commissioni", default=5.0)
    date_account_created = fields.Datetime(string="Data creazione")
    cookie_duration = fields.Integer(string="Durata Cookie")
    exclude = fields.Boolean(string="Escluso dalle commissioni")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente", required=True)
    commission_id = fields.One2many(
        comodel_name='netaddiction.partner.affiliate.commission',
        inverse_name='affiliate_id',
        string='Commissioni')
    orders_history = fields.One2many('netaddiction.partner.affiliate.order.history', 'affiliate_id', string='ordini generati')
    tot = fields.Float(string='Totale generale', compute="_compute_tot")
    tot_completed = fields.Float(string='Totale ordini completati', compute="_compute_tot_completed")
    tot_problems = fields.Float(string='Quantità ordini problemi', compute="_compute_tot_problems")
    tot_cancelled = fields.Float(string='Quantità ordini cancellati', compute="_compute_tot_cancelled")
    tot_gift_history = fields.Float(string='Commissioni totali ottenute', default=0.0)

    @api.model
    def create(self, values):
        myself = super(Affiliate, self).create(values)
        self.env['res.partner'].search([('id', '=', values['partner_id'])])[0]['affiliate_id'] = myself
        return myself

    @api.depends('orders_history')
    def _compute_tot(self):
        for record in self:
            tot = 0.0
            for order in record.orders_history:
                tot += order.order_id.amount_total
            record.tot = tot

    @api.depends('orders_history')
    def _compute_tot_completed(self):
        for record in self:
            tot = 0.0
            for order in record.orders_history:
                if order.order_id.state == 'done':
                    tot += order.order_id.amount_total
            record.tot_completed = tot

    @api.depends('orders_history')
    def _compute_tot_problems(self):
        for record in self:
            tot = 0.0
            for order in record.orders_history:
                if order.order_id.state == 'problem':
                    tot += order.order_id.amount_total
            record.tot_problems = tot

    @api.depends('orders_history')
    def _compute_tot_cancelled(self):
        for record in self:
            tot = 0.0
            for order in record.orders_history:
                if order.order_id.state == 'cancel':
                    tot += order.order_id.amount_total
            record.tot_cancelled = tot

    def get_hashed(self):
        salt = self.env["ir.config_parameter"].search([("key", "=", "affiliate.salt")]).value
        hashids = Hashids(salt=salt)
        return hashids.encode(self.control_code)

    def check_order(self, order):
        gift_gained = 0.0
        if not self.exclude:
            if self.commission_id:
                for commission in self.commission_id:
                    expression = commission.expression_id
                    dom = expression.find_products_domain()
                    prod_ids = [pl.id for pl in self.env['product.product'].search(dom)]
                    for ol in order.order_line:
                        if ol.product_id.id in prod_ids:
                            gift_gained += (ol.price_total / 100) * commission.commission_percent
            else:
                for ol in order.order_line:
                    gift_gained += (ol.price_total / 100) * self.commission_percent

        return gift_gained


class AffiliateCustomer(models.Model):
    _inherit = 'res.partner'
    affiliate_id = fields.Many2one(comodel_name='netaddiction.partner.affiliate', string='Dati Affiliato')

    @api.constrains('affiliate_id')
    def _constrains_set_a_id(self):
        if len(self.affiliate_id) > 1:
            raise openerp.exceptions.ValidationError('Questo cliente è già un affiliato!')

    @api.multi
    def new_customer_affiliate(self):

        view_id = self.env.ref('netaddiction_customer.netaddiction_sales_affiliate_form').id
        return {
            'name': 'Nuova Affiliato',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'form')],
            'res_model': 'netaddiction.partner.affiliate',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_id': self.id,
            },
        }


class AffiliateCommission(models.Model):
    _name = "netaddiction.partner.affiliate.commission"

    commission_percent = fields.Float(string="Percentuale commissioni")
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Filtro prodotti')
    affiliate_id = fields.Many2one(comodel_name='netaddiction.partner.affiliate', string='Affiliato', required=True)

    @api.one
    @api.constrains('commission_percent')
    def _check_value(self):
        if self.commission_percent < 0.0 or self.commission_percent > 100.0:
            raise ValidationError("Percentuale commissioni deve essere compreso tra 0 e 100")


class AffiliateOrderHistory(models.Model):
    _name = "netaddiction.partner.affiliate.order.history"

    order_id = fields.Many2one(comodel_name='sale.order', string='Ordine', index=True, copy=False, required=True)
    affiliate_id = fields.Many2one(comodel_name='netaddiction.partner.affiliate', string='Affiliate', index=True, copy=False, required=True)
    commission = fields.Float(string="Commissioni guadagnate")
    assigned = fields.Boolean(string="Commissioni assegnate")


class AffiliateUtilities(models.TransientModel):
    _name = "netaddiction.partner.affiliate.utilities"

    def order_to_affiliate(self, order_id, hashed_affiliate_id):
        salt = self.env["ir.config_parameter"].search([("key", "=", "affiliate.salt")]).value

        hashids = Hashids(salt=salt)

        order = self.env["sale.order"].search([("id", "=", order_id)])
        affiliate = self.env["netaddiction.partner.affiliate"].search([("control_code", "=", hashids.decode(hashed_affiliate_id)[0])])
        if order and affiliate:
            order_ids = [oh.order_id.id for oh in affiliate.orders_history]
            if order.id not in order_ids:
                commission_value = affiliate.check_order(order)
                self.env["netaddiction.partner.affiliate.order.history"].create({
                    'order_id': order.id,
                    'affiliate_id': affiliate.id,
                    'commission': commission_value,
                    'assigned': False})

    @api.model
    def register_commissions(self):
        orders = self.env["netaddiction.partner.affiliate.order.history"].search([("assigned", "=", False)])
        for order in orders:
            if not order.affiliate_id.exclude and order.order_id.state == "done" and (datetime.now() - datetime.strptime(order.order_id.date_done, '%Y-%m-%d %H:%M:%S')) > timedelta(days=15):
                order.affiliate_id.partner_id.add_gift_value(order.commission, "Affiliate")
                order.affiliate_id.tot_gift_history += order.commission
                order.assigned = True


class Order(models.Model):
    _inherit = 'sale.order'

    date_done = fields.Datetime(string="Data messo in completato")
