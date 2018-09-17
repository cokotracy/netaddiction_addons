# -*- coding: utf-8 -*-

from openerp import models, fields, api

class CustomerLoyalty(models.Model):

    """
    classe base della fidelizzazione composta da:
    - partner_id: il cliente a cui è associata la raccolta punti
    - points: valore in punti
    - money: valore in denaro (equivalente ai punti secondo la configurazione)
    - logs: lista di log sulle operazione di aggiunta e rimozione punti/denaro
    """

    _name = "customer.loyalty"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True)
    points = fields.Float(string="Points value")
    money = fields.Float(string="Money value")
    logs = fields.One2many(
        comodel_name='customer.loyalty.log',
        inverse_name='customer_loyalty_id',
        string='History')

    @api.multi
    def name_get(self):
        res = []

        for s in self:
            res.append((s.id, ' => '.join([s.partner_id.name, str(s.points)])))

        return res

    @api.model
    def create(self, values):
        # creo subito il rigo
        myself = super(CustomerLoyalty, self).create(values)
        # vado a creare il log di creazione
        res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
        val = myself.money
        loyalty_type = 'money'
        if res['points_money'] == 'points':
            val = myself.points
            loyalty_type = 'points'
        attrs = {
            'customer_loyalty_id': myself.id,
            'value': val,
            'loyalty_type': loyalty_type,
            'date': fields.datetime.now(),
            'what': 'add',
            'author_id': self.env.uid
        }
        self.env['customer.loyalty.log'].create(attrs)
        return myself

    @api.multi
    def write(self, values):
        res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
        equal = self.env['customer.loyalty.settings'].get_default_conversion_points_money('conversion_points_money')
        for s in self:
            this_value = s.money
            new_value = values.get('money', 0)
            loyalty_type = 'money'
            if res['points_money'] == 'points':
                this_value = s.points
                new_value = values.get('points', 0)
                loyalty_type = 'points'
            log_value = new_value - this_value
            if log_value > 0:
                what = 'add'
            else:
                what = 'sub'
            # loggo il cambiamento
            if not self.env.context.get('skip_loyalty_log', False):
                attrs = {
                    'customer_loyalty_id': s.id,
                    'value': log_value,
                    'loyalty_type': loyalty_type,
                    'date': fields.datetime.now(),
                    'what': what,
                    'author_id': self.env.uid
                }
                self.env['customer.loyalty.log'].create(attrs)

                # converto il valore punti/soldi o viceversa ricordando che è sempre 1 punto che vale soldi
                e = equal['conversion_points_money']

                if res['points_money'] == 'points':
                    convert_value = new_value * float(e)
                    s.with_context({'skip_loyalty_log': True}).money = convert_value
                else:
                    convert_value = new_value / float(e)
                    s.ith_context({'skip_loyalty_log': True}).points = convert_value

        return super(CustomerLoyalty, self).write(values)

class CustomerLoyaltyLog(models.Model):

    """
    Classe per i log sulle operazioni di aggiunta e rimozione punti/denaro
    """

    _name = "customer.loyalty.log"

    customer_loyalty_id = fields.Many2one(
        comodel_name="customer.loyalty",
        string="Customer Loyalty")
    value = fields.Float(string="Value")
    loyalty_type = fields.Selection(
        selection=(('points', 'Points'), ('money', 'Money')),
        string="Type")
    what = fields.Selection(
        selection=(('add', 'Add'), ('sub', 'Sub')),
        string="What")
    date = fields.Datetime(string="Data")
    author_id = fields.Many2one(comodel_name='res.users', string='User', required=True)

class CustomerLoyaltyAdd(models.TransientModel):

    """
    Classe transient per le operazioni di aggiunta.
    Viene usata per le viste e per evitare di duplicare un customer.loyalty
    """

    _name = 'customer.loyalty.add'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True)
    value = fields.Float(string="Value")
    # TODO: compute sul tipo settings
    loyalty_type = fields.Selection(
        selection=(('points', 'Points'), ('money', 'Money')),
        string="Type")

class CustomerLoyaltySub(models.TransientModel):

    """
    Classe transient per le operazioni di rimozione.
    Viene usata per le viste e per evitare di duplicare un customer.loyalty
    """

    _name = 'customer.loyalty.sub'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True)
    value = fields.Float(string="Value")
    # TODO: compute sul tipo settings
    loyalty_type = fields.Selection(
        selection=(('points', 'Points'), ('money', 'Money')),
        string="Type")

class PartnerLoyalty(models.Model):
    """
    Aggiunge il campo raccolta punti/denaro al cliente
    """

    _inherit = "res.partner"

    loyalty_value = fields.Float(string="Loyalty Value", compute="_get_loyalty_value")

    @api.one
    def _get_loyalty_value(self):
        """
        Se presente recupera il rigo con la fidelizzazione,
        altrimenti lo crea
        prende il valore e lo mostra
        """

        # se è un idirizzo non deve creare
        if self.parent_id:
            self.loyalty_value = 0
            return True

        loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.id)])
        if len(loyalty) == 0:
            # non c'è alcuna fidelizzazione, la creo
            attrs = {
                'partner_id': self.id,
                'points': 0,
                'money': 0
            }
            res = self.env['customer.loyalty'].create(attrs)
            loyalty = res

        value = loyalty.money
        res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
        loyalty_type = res['points_money']
        if loyalty_type == 'points':
            value = loyalty.points

        self.loyalty_value = value

    @api.multi
    def open_loyalty(self):
        loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.id)])
        view_id = self.env.ref('customer_loyalty.custoemr_loyalty_form_view').id
        return {
            'name': 'Loyalty',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'customer.loyalty',
            'res_id': loyalty.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': {},
            'target': 'new',
        }
