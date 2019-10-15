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
    company_id = fields.Many2one('res.company', 'Società', default=1)

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
                    s.with_context({'skip_loyalty_log': True}).write({'money': self.env['customer.loyalty'].convert_points_money(new_value, 'money')})
                else:
                    s.with_context({'skip_loyalty_log': True}).write({'points': self.env['customer.loyalty'].convert_points_money(new_value, 'points')})

        return super(CustomerLoyalty, self).write(values)

    @api.model
    def cron_loyalty_earned(self):
        """
        Questo cron assegna i punti/soldi degli ordini completati
        """
        state = self.env['customer.loyalty.settings'].get_default_order_state('order_state')['order_state']
        # prendo gli ordini che sono in completato che non hanno assegnati i punti e che hanno i punti maggiori di zero (con questo elimino i vecchi ordini e quelli che non serve analizzare)
        orders = self.env['sale.order'].search([('state', '=', state), ('loyalty_earned_assigned', '=', False), ('loyalty_earned', '>', 0)])
        res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
        loyalty_type = res['points_money']
        for order in orders:
            value = 0
            loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', order.partner_id.id)])
            if loyalty_type == 'points':
                value = order.loyalty_earned
                loyalty.with_context({'order_id': order.id}).write({'points': loyalty.points + value})
            else:
                value = self.env['customer.loyalty'].convert_points_money(order.loyalty_earned, 'money')
                loyalty.with_context({'order_id': order.id}).write({'money': loyalty.money + value})
            order.loyalty_earned_assigned = True

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
    company_id = fields.Many2one('res.company', 'Società', default=1)

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
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).write({'points': loyalty.points + self.value}) 
            else:
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).write({'money': loyalty.money + self.value})
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
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).write({'points': loyalty.points - self.value})
            else:
                if self.value > loyalty.money:
                    raise UserError(_('Entered value is greater than the existing one'))
                loyalty.with_context({'note': self.note, 'internal_note': self.internal_note}).write({'money': loyalty.money - self.value})
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

                cl = self.env['customer.loyalty'].create(attrs)      

                loyalty = cl

            # qua se ci sono gift converto il loro valore in punti e li azzero.
            try:
                # try perchè questo modulo non può dipendere direttamente da gift
                if self.total_gift > 0:
                    if loyalty_type == 'points':
                        total = loyalty.points + int(self.env['customer.loyalty'].convert_points_money(self.total_gift, 'points'))
                        loyalty.with_context({'note': 'Conversione Gift'}).write({'points': total})
                    else:
                        loyalty.with_context({'note': 'Conversione Gift'}).write({'money': loyalty.money + self.total_gift})
                    for line in self.gift_ids:
                        line.unlink()
            except:
                pass  

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

class LoyaltyOrders(models.Model):
    """
    Gestisce i punti negli ordini
    """
    _inherit = "sale.order"

    loyalty_used = fields.Float(string="Loyaltay used", default=0)
    loyalty_earned = fields.Float(string="Loyalty earned", default=0)
    loyalty_earned_assigned = fields.Boolean(string="Loyalty Assigned", default=False)
    loyalty_prev = fields.Float(string="Previous loyalty used", default=0)
    loyalty_used_logged = fields.Boolean(string="Loyalty used Logged", default=False)

    @api.constrains('loyalty_used')
    @api.one
    def _loyalty_used(self):
        """
        una volta assegnati i punti, questa funzione fa il calcolo ed applica lo sconto sul totale dell'ordine.
        """
        obj = self.env['customer.loyalty'].search([('partner_id', '=', self.partner_id.id)])
        # controllo i punti
        if len(obj) > 0:
            if self.loyalty_used < 0:
                self.loyalty_used = 0
            res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
            loyalty_type = res['points_money']
            if loyalty_type == 'points':
                if self.loyalty_used > obj.points:
                    # azzero i punti e non lancio nessuna eccezione per evitare problemi
                    self.loyalty_used = 0
            else:
                if self.loyalty_used > obj.money:
                    # azzero i punti e non lancio nessuna eccezione per evitare problemi
                    self.loyalty_used = 0

            money = self.loyalty_used
            if loyalty_type == 'points':
                money = self.env['customer.loyalty'].convert_points_money(self.loyalty_used, 'money')
            # uso la funzione così sono sicuro che prende il valore corretto del totale
            self._amount_all()

            # tolgo i punti dall'account utente
            if self.loyalty_used > 0:
                # devo sottrarre
                if loyalty_type == 'points':
                    obj.with_context({'skip_loyalty_log': True}).write({'points': obj.points - self.loyalty_used})
                    obj.with_context({'skip_loyalty_log': True}).write({'money': self.env['customer.loyalty'].convert_points_money(obj.points, 'money')})
                else:
                    obj.with_context({'skip_loyalty_log': True}).write({'money': obj.money - money})
                    obj.with_context({'skip_loyalty_log': True}).write({'points': self.env['customer.loyalty'].convert_points_money(obj.money, 'points')})
            else:
                # devo aggiungere
                if loyalty_type == 'points':
                    obj.with_context({'skip_loyalty_log': True}).write({'points': obj.points + self.loyalty_prev})
                    obj.with_context({'skip_loyalty_log': True}).write({'money': self.env['customer.loyalty'].convert_points_money(obj.points, 'money')})
                else:
                    obj.with_context({'skip_loyalty_log': True}).write({'money': obj.money + self.loyalty_prev})
                    obj.with_context({'skip_loyalty_log': True}).write({'points': self.env['customer.loyalty'].convert_points_money(obj.money, 'points')})

            self.loyalty_prev = self.loyalty_used

    @api.constrains('amount_total')
    @api.one
    def _change_amount_total(self):
        """
        Ogni volta che cambia amount total (il totale dell'ordine) ricalcola il suo valore se ci sono loyalty_used

        context:
            {'pass_amount_total': True} => serve per evitare il calcolo dei punti
        """

        if self.env.context.get('pass_amount_total', False):
            return True
        new_amount = self.amount_total
        if self.loyalty_used > 0:
            res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
            loyalty_type = res['points_money']
            money = self.loyalty_used
            if loyalty_type == 'points':
                money = self.env['customer.loyalty'].convert_points_money(self.loyalty_used, 'money')
            # sarebbe il valore corretto ma nel nostro sistema legacy dobbiamo usare la prossiam riga if money > self.amount_total:
            if money > self.simulate_total_amount():
                # se i punti inseriti valogno più del totale dell'ordine non li faccio applicare
                self.loyalty_used = 0
                money = 0
            new_amount = float(self.amount_total) - float(money)
            self.with_context({'pass_amount_total': True}).amount_total = new_amount

        # assegno i punti
        percentage = self.env['customer.loyalty.settings'].get_default_revenues_percentage('revenues_percentage')['revenues_percentage']
        if new_amount > 0:
            money_value = (new_amount * percentage) / 100
            points_value = self.env['customer.loyalty'].convert_points_money(money_value, 'points')
            # metto il valore in punti
            self.loyalty_earned = int(points_value)

    @api.constrains('state')
    @api.one
    def _log_loyalty_used(self):
        """
        Logga l'uso dei punti
        """
        if self.state == 'sale' and not self.loyalty_used_logged:
            self.loyalty_used_logged = True
            loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.partner_id.id)])
            if len(loyalty) == 1 and self.loyalty_used > 0:
                res = self.env['customer.loyalty.settings'].get_default_points_money('points_money')
                loyalty_type = res['points_money']
                if loyalty_type == 'points':
                    points_value = self.loyalty_used
                    money_value = self.env['customer.loyalty'].convert_points_money(self.loyalty_used, 'money')
                else:
                    money_value = self.loyalty_used
                    points_value = self.env['customer.loyalty'].convert_points_money(self.money_value, 'points')
                attrs = {
                    'customer_loyalty_id': loyalty.id,
                    'points_value': (0 - points_value),
                    'money_value': (0 - money_value),
                    'date': fields.datetime.now(),
                    'what': 'sub',
                    'author_id': self.env.uid,
                    'note': '',
                    'internal_note': '',
                    'order_id': self.id
                }
                self.env['customer.loyalty.log'].create(attrs)

    @api.multi
    def open_loyalty(self):
        loyalty = self.env['customer.loyalty'].search([('partner_id.id', '=', self.partner_id.id)])
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
