# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError

class CustomerLoyalty(models.Model):

    """
    classe base della fidelizzazione composta da:
    - partner_id: il cliente a cui è associata la raccolta punti
    - points: valore in punti
    - money: valore in denaro (equivalente ai punti secondo la configurazione)
    - logs: lista di log sulle operazione di aggiunta e rimozione punti/denaro

    context:
        write: {'skip_loyalty_log': True} => non logga le modifiche
               {'note': <text>} => <text> testo della nota
               {'internal_note': <text>} => <text> testo della nota interna
               {'order_id': <order_id>} => <order_id> id dell'ordine

        unlink: {'real_unlink': True} => cancella definitivamente la loyalty
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
    def convert_points_money(self, value, to):
        """
        Converte il valore value in points o money
        to: points/money valore in uscita dalla funzione, se money in entrata devi avere points e viceversa.
        """
        # valore di un point in money (sempre così da config)
        equal = self.env['customer.loyalty.settings'].get_default_conversion_points_money('conversion_points_money')
        e = equal['conversion_points_money']
        if to == 'money':
            return value * float(e)
        else:
            return value / float(e)

    @api.model
    def create(self, values):
        res = self.search([('partner_id', '=', int(values['partner_id']))])
        if len(res) > 0:
            # se è già presente ritorno false per non creare casini
            return False
        # creo subito il rigo
        myself = super(CustomerLoyalty, self).create(values)
        # vado a creare il log di creazione
        text_welcome = self.env['customer.loyalty.settings'].get_default_text_welcome('text_welcome')
        attrs = {
            'customer_loyalty_id': myself.id,
            'points_value': myself.points,
            'money_value': myself.money,
            'date': fields.datetime.now(),
            'what': 'add',
            'author_id': self.env.uid,
            'note': text_welcome['text_welcome']
        }
        self.env['customer.loyalty.log'].create(attrs)
        return myself

    @api.one
    def unlink(self):
        """
        tecnicamente non facciamo cancellare una loyalty dal backoffice,
        semmai si usa un contesto

        context:
            {'real_unlink': True} => cancella definitivamente la loyalty
        """
        if self.env.context.get('real_unlink', False):
            return super(CustomerLoyalty, self).unlink()

        raise UserError(_("You can't delete object."))

    @api.multi
    def add_value(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.loyalty.add',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'context': {'default_partner_id': self.partner_id.id},
            'target': 'new', }

    @api.multi
    def remove_value(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.loyalty.sub',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'context': {'default_partner_id': self.partner_id.id},
            'target': 'new', }

    @api.multi
    def write(self, values):
        """
        context:
            {'skip_loyalty_log': True} => non logga le modifiche

            {'note': <text>} => <text> testo della nota
            {'internal_note': <text>} => <text> testo della nota interna
            {'order_id': <order_id>} => <order_id> id dell'ordine
        """
        res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')

        for s in self:
            this_value = s.money
            new_value = values.get('money', 0)
            money_value = new_value - this_value
            points_value = self.env['customer.loyalty'].convert_points_money(money_value, 'points')

            if res['points_money'] == 'points':
                this_value = s.points
                new_value = values.get('points', 0)
                points_value = new_value - this_value
                money_value = self.env['customer.loyalty'].convert_points_money(points_value, 'money')

            if (new_value - this_value) > 0:
                what = 'add'
            else:
                what = 'sub'

            # loggo il cambiamento
            if not self.env.context.get('skip_loyalty_log', False):
                attrs = {
                    'customer_loyalty_id': s.id,
                    'points_value': points_value,
                    'money_value': money_value,
                    'date': fields.datetime.now(),
                    'what': what,
                    'author_id': self.env.uid,
                    'note': self.env.context.get('note', ''),
                    'internal_note': self.env.context.get('internal_note', ''),
                    'order_id': self.env.context.get('order_id', False)
                }
                self.env['customer.loyalty.log'].create(attrs)

                # converto il valore punti/soldi o viceversa ricordando che è sempre 1 punto che vale soldi

                if res['points_money'] == 'points':
                    s.with_context({'skip_loyalty_log': True}).money = self.env['customer.loyalty'].convert_points_money(new_value, 'money')
                else:
                    s.with_context({'skip_loyalty_log': True}).points = self.env['customer.loyalty'].convert_points_money(new_value, 'points')

        return super(CustomerLoyalty, self).write(values)

class CustomerLoyaltyLog(models.Model):

    """
    Classe per i log sulle operazioni di aggiunta e rimozione punti/denaro
    """

    _name = "customer.loyalty.log"

    customer_loyalty_id = fields.Many2one(
        comodel_name="customer.loyalty",
        string="Customer Loyalty")
    points_value = fields.Float(string="Value Points")
    money_value = fields.Float(string="Value Money")
    what = fields.Selection(
        selection=(('add', 'Add'), ('sub', 'Sub')),
        string="What")
    date = fields.Datetime(string="Data")
    author_id = fields.Many2one(comodel_name='res.users', string='User', required=True)
    note = fields.Char(string="Note")
    internal_note = fields.Char(string="Internal Note")
    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Order")

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
    value = fields.Float(string="Adding Value")
    loyalty_type = fields.Selection(
        selection=(('points', 'Points'), ('money', 'Money')),
        string="Type")
    note = fields.Char(string="Note")
    internal_note = fields.Char(String="Internal Note")

    @api.multi
    def execute(self):
        self.ensure_one()
        loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.partner_id.id)])
        if len(loyalty) == 1:
            if self.loyalty_type == 'points':
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).points = loyalty.points + self.value
            else:
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).money = loyalty.money + self.value
        else:
            raise UserError(_('There is a problem with loyalty for this customer. Contact Administrator.'))


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
    value = fields.Float(string="Removing Value")
    loyalty_type = fields.Selection(
        selection=(('points', 'Points'), ('money', 'Money')),
        string="Type")
    note = fields.Char(string="Note")
    internal_note = fields.Char(String="Internal Note")

    @api.multi
    def execute(self):
        self.ensure_one()
        loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.partner_id.id)])
        if len(loyalty) == 1:
            if self.loyalty_type == 'points':
                if self.value > loyalty.points:
                    raise UserError(_('Entered value is greater than the existing one'))
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).points = loyalty.points - self.value
            else:
                if self.value > loyalty.money:
                    raise UserError(_('Entered value is greater than the existing one'))
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).money = loyalty.money - self.value
        else:
            raise UserError(_('There is a problem with loyalty for this customer. Contact Administrator.'))

class PartnerLoyalty(models.Model):
    """
    Aggiunge il campo raccolta punti/denaro al cliente

    context:
        _get_loyalty_value: {'create_new_loyalty': True} => crea la loyalty base
    """

    _inherit = "res.partner"

    loyalty_value = fields.Float(string="Loyalty Value", compute="_get_loyalty_value")
    loyalty_name = fields.Char(string="Loyalty Name", compute="_get_loyalty_name")

    @api.one
    def _get_loyalty_value(self):
        """
        Se presente recupera il rigo con la fidelizzazione,
        altrimenti lo crea
        prende il valore e lo mostra

        context: {'create_new_loyalty': True} => crea la loyalty base
        """

        # se è un indirizzo non deve creare
        if self.parent_id:
            self.loyalty_value = 0
            return True

        loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.id)])

        res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
        loyalty_type = res['points_money']

        if self.env.context.get('create_new_loyalty', False):
            if len(loyalty) == 0:
                # non c'è alcuna fidelizzazione, la creo
                welcome_points = self.env['customer.loyalty.settings'].get_default_welcome_points('welcome_points')

                if loyalty_type == 'points':
                    attrs = {
                        'partner_id': self.id,
                        'points': welcome_points['welcome_points'],
                        'money': self.env['customer.loyalty'].convert_points_money(welcome_points['welcome_points'], 'money')
                    }
                else:
                    attrs = {
                        'partner_id': self.id,
                        'points': self.env['customer.loyalty'].convert_points_money(welcome_points['welcome_points'], 'points'),
                        'money': welcome_points['welcome_points']
                    }

                res = self.env['customer.loyalty'].create(attrs)
                loyalty = res

        value = loyalty.money

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

    @api.one
    def _get_loyalty_name(self):
        res = self.env['customer.loyalty.settings'].get_default_text_fe('text_fe')['text_fe']
        self.loyalty_name = res
