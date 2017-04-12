# -*- coding: utf-8 -*-
from openerp import SUPERUSER_ID, api, fields, models
from openerp.exceptions import ValidationError
from math import floor
import StringIO
import base64


class CatalogOffer(models.Model):

    _name = "netaddiction.specialoffer.catalog"

    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=False)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env["res.company"].browse(1).id)
    author_id = fields.Many2one(comodel_name='res.users', string='Autore', required=True, default=lambda self: self.env.user.id)
    date_start = fields.Datetime('Start Date', help="Data di inizio della offerta, se non impostata l'offerta comincia subito", required=False)
    date_end = fields.Datetime('End Date', help="Data di fine dell'offerta", required=True)
    priority = fields.Selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')], string='Priorità', default=1, required=True)
    qty_max_buyable = fields.Integer(string='Quantità massima acquistabile', help="Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato")
    qty_limit = fields.Integer(string='Quantità limite', help="Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato")
    qty_min = fields.Integer(string='Quantità minima acquisto', help="Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.")
    qty_selled = fields.Float(string='Quantità venduta', default=0.0, compute="_compute_qty_selled")
    offer_type = fields.Selection([(1, 'Prezzo Fisso'), (2, 'Percentuale')], string='Tipo Offerta', default=2)
    fixed_price = fields.Float(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale", default=10)
    percent_rounded_down = fields.Boolean(string='Arrotondamento', help="Arrotondamento prezzo offerta per difetto", default=True)
    one_day = fields.Boolean(string='Offerta del giorno', help="Flaggare se si vuole che i prodotti in questa offerta compaiano nella pagina offerte del giorno", default=False)
    products_list = fields.One2many('netaddiction.specialoffer.offer_catalog_line', 'offer_catalog_id', string='Lista prodotti', domain=['|', ('active', '=', False), ('active', '=', True)])
    end_cron_job = fields.Integer()
    start_cron_job = fields.Integer()

    qty_limit_is_available = fields.Boolean(string="La quantità limite è quella disponibile", default=False)

    pid_list = fields.Binary(string="Lista id prodotti")

    @api.one
    def get_pid_list(self):
        ids = []
        for product in self.products_list:
            if product.active:
                ids.append(product.product_id.id)

        text = ','.join(str(x) for x in ids)
        output = StringIO.StringIO()
        output.write(text)

        self.pid_list = base64.b64encode(output.getvalue().encode("utf8"))
        output.close()

    _sql_constraints = [
        ('name', 'unique(name)', 'Nome offerta deve essere unico!'),
    ]

    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active:
            for pl in self.products_list:
                pl.active = False

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):

        if(self.date_start and self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")
        for cron in self.env['ir.cron'].search([('id', '=', self.end_cron_job), ('active', '=', True)]):
            cron.nextcall = self.date_end
        found_cron = False
        for cron in self.env['ir.cron'].search([('id', '=', self.start_cron_job), ('active', '=', True)]):
            cron.nextcall = self.date_start
            found_cron = True
        if not found_cron and self.date_start:

            nextcall = self.date_start
            name = "[Inizio]Cron job per offerta CATALOGO id %s" % self.id
            self.start_cron_job = self.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.catalog',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([self.id]),
                'numbercall': "1",

            })

    @api.one
    @api.constrains('priority')
    def _check_priority(self):
        for pl in self.products_list:
            pl.priority = self.priority

    @api.model
    def create(self, values):

        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        e creo i cron
        """
        now = fields.Datetime.now()
        if (values['date_start'] and values['date_start'] <= now):
            raise ValidationError("Data inizio offerta non può essere prima della data e ora attuale")
        elif (values['date_end'] and values['date_end'] <= now):
            raise ValidationError("Data fine offerta non può essere prima della data e ora attuale")

        res = super(CatalogOffer, self).create(values)

        nextcall = res.date_end
        name = "[Scadenza]Cron job per offerta CATALOGO id %s" % res.id
        res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
            'name': name,
            'user_id': SUPERUSER_ID,
            'model': 'netaddiction.specialoffer.catalog',
            'function': 'turn_off',
            'nextcall': nextcall,
            'args': repr([res.id]),
            'numbercall': "1",
        })
        if res.date_start and res.date_start > now:
            res.active = False
            for pl in res.products_list:
                pl.active = False

            nextcall = res.date_start
            name = "[Inizio]Cron job per offerta CATALOGO id %s" % res.id
            res.start_cron_job = res.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.catalog',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall': "1",

            })
        else:
            res.turn_on()

        return res

    @api.one
    def populate_products_from_expression(self):
        if self.expression_id:
            dom = self.expression_id.find_products_domain()
            ids = []
            to_add = []
            for pl in self.products_list:
                ids.append(pl.product_id.id)

            for prod in self.env['product.product'].search(dom):
                if(prod.id not in ids):
                    to_add.append(self.env['netaddiction.specialoffer.offer_catalog_line'].create({'product_id': prod.id, 'offer_catalog_id': self.id, 'qty_max_buyable': self.qty_max_buyable, 'qty_limit': self.qty_limit, 'qty_min': self.qty_min, 'offer_type': self.offer_type, 'percent_discount': self.percent_discount, 'fixed_price': self.fixed_price, 'priority': self.priority}))

    @api.multi
    def remove_products(self):
        # in caso serva di cancellare tutte le order line
        # for pl2 in self.env['netaddiction.specialoffer.offer_catalog_line'].search([("create_uid","=",1)]):
        #     pl2.unlink()

        for offer in self:
            for pl in offer.products_list:
                pl.unlink()

    @api.multi
    def modify_products(self):
        for pl in self.products_list:
            pl.qty_max_buyable = self.qty_max_buyable
            pl.qty_limit = self.qty_limit
            pl.qty_min = self.qty_min
            pl.offer_type = self.offer_type
            pl.percent_discount = self.percent_discount
            pl.fixed_price = self.fixed_price
            pl.priority = self.priority

    @api.one
    def turn_off(self):
        self.write({'active': False})
        for pl in self.products_list:
            pl.active = False

    @api.one
    def turn_on(self):
        if not self.active:
            for pl in self.env['netaddiction.specialoffer.offer_catalog_line'].search([('offer_catalog_id', '=', self.id), ('active', '=', False)]):
                if self.qty_limit_is_available:
                    pl.qty_limit = pl.product_qty_available_now if pl.product_qty_available_now > 0 else 0
                    pl.active = pl.product_qty_available_now > 0
                else:
                    pl.active = True

            self.write({'active': True})

    @api.multi
    def _compute_qty_selled(self):
        for offer in self:
            temp = 0.0
            for pl in offer.products_list:
                temp += pl.qty_selled

            # search for inactive offers
            offer.qty_selled = temp

    @api.one
    def unlink(self):
        self.turn_off()


class OfferCatalogLine(models.Model):

    _name = "netaddiction.specialoffer.offer_catalog_line"
    _order = "priority"

    active = fields.Boolean(default=False,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_catalog_id = fields.Many2one('netaddiction.specialoffer.catalog', string='Offerta catalogo', index=True, copy=False, required=True)
    qty_max_buyable = fields.Integer(string='Quantità massima acquistabile', help="Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer(string='Quantità limite', help="Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_min = fields.Integer(string='Quantità minima acquisto', help="Quantità minima di prodotti da inserire nel carrello per attivare l'offerta.", required=True)
    fixed_price = fields.Float(string="Prezzo fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale", default=10)
    offer_type = fields.Selection([(1, 'Prezzo Fisso'), (2, 'Percentuale')], string='Tipo Offerta', default=2)
    qty_selled = fields.Float(string='Quantità venduta', default=0.0)
    priority = fields.Integer(string="priorità", default=0)
    company_id = fields.Many2one('res.company', string='Azienda', related='offer_catalog_id.company_id', store=True)

    # campo related per il prezzo medio di acquisto
    product_offer_price_fake = fields.Float(string="Prezzo Offerta", compute="compute_offer_price_fake", store=False, default=0)
    med_inventory_value_intax = fields.Float(related="product_id.med_inventory_value_intax", store=False)
    product_qty_available_now = fields.Integer(related="product_id.qty_available_now", store=False)

    @api.one
    @api.constrains('fixed_price', 'offer_type')
    def _check_fixed_price(self):
        if self.offer_type == 1 and self.fixed_price <= 0:
            raise ValidationError("Il valore del prezzo fisso non può essere minore  o uguale di zero")

    @api.one
    @api.constrains('percent_discount', 'offer_type')
    def _check_percent_discount(self):
        if self.offer_type == 2 and (self.percent_discount <= 0 or self.percent_discount > 100):
            raise ValidationError("Il valore dello sconto percentuale non può essere minore di 0 o maggiore di 100")

    @api.one
    @api.constrains('offer_catalog_id')
    def _check_priority(self):
        self.priority = self.offer_catalog_id[0].priority
        self.offer_type = self.offer_catalog_id[0].offer_type

    @api.one
    def compute_offer_price_fake(self):

        if self.offer_type == 1:
            self.product_offer_price_fake = self.fixed_price
        else:
            temp = (self.product_id.list_price - (self.product_id.list_price / 100) * self.percent_discount)
            self.product_offer_price_fake = floor(temp * 10) / 10


class ShoppingCartOffer(models.Model):

    _name = "netaddiction.specialoffer.cart"

    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=False)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    author_id = fields.Many2one(comodel_name='res.users', string='Autore', required=True, default=lambda self: self.env.user.id)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env["res.company"].browse(1).id)
    date_start = fields.Datetime('Start Date', help="Data di inizio della offerta, se non impostata l'offerta comincia subito", required=False)
    date_end = fields.Datetime('End Date', help="Data di fine dell'offerta", required=True)
    priority = fields.Selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')], string='Priorità', default=1, required=True)
    qty_max_buyable = fields.Integer(string='Quantità massima acquistabile', help="Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer(string='Quantità limite', help="Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_selled = fields.Integer(string='Quantità venduta', default=0.0, compute="_compute_qty_selled")
    offer_type = fields.Selection([(1, 'Bundle'), (2, 'n x m'), (3, 'n x prezzo'), (4, 'Spedizioni Gratis')], string='Tipo Offerta', default=2, required=True)
    n = fields.Integer(string="N")
    m = fields.Integer(string="M")
    bundle_price = fields.Float(string="Prezzo bundle")
    n_price = fields.Float(string="Prezzo Prodotti")
    products_list = fields.One2many('netaddiction.specialoffer.offer_cart_line', 'offer_cart_id', string='Lista prodotti', domain=['|', ('active', '=', False), ('active', '=', True)])
    end_cron_job = fields.Integer()
    start_cron_job = fields.Integer()

    qty_limit_is_available = fields.Boolean(string="La quantità limite è quella disponibile", default=False)

    pid_list = fields.Binary(string="Lista id prodotti")

    _sql_constraints = [
        ('name', 'unique(name)', 'Nome offerta deve essere unico!'),
    ]

    @api.one
    def get_pid_list(self):
        ids = []
        for product in self.products_list:
            if product.active:
                ids.append(product.product_id.id)

        text = ','.join(str(x) for x in ids)
        output = StringIO.StringIO()
        output.write(text)

        self.pid_list = base64.b64encode(output.getvalue().encode("utf8"))
        output.close()

    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active:
            for pl in self.products_list:
                pl.active = False

    @api.one
    @api.constrains('priority')
    def _check_priority(self):
        for pl in self.products_list:
            pl.priority = self.priority

    @api.one
    @api.constrains('n', 'm', 'offer_type')
    def _check_n_m(self):
        if(self.offer_type == 2):
            if(self.n <= 0 or self.m <= 0):
                raise ValidationError("n e m devono essere  > 0")
            if(self.n <= self.m):
                raise ValidationError("n deve essere maggiore di m! (es. 3x2)")

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):

        if(self.date_start and self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")
        for cron in self.env['ir.cron'].search([('id', '=', self.end_cron_job), ('active', '=', True)]):
            cron.nextcall = self.date_end
        found_cron = False
        for cron in self.env['ir.cron'].search([('id', '=', self.start_cron_job), ('active', '=', True)]):
            cron.nextcall = self.date_start
            found_cron = True
        if not found_cron and self.date_start:

            nextcall = self.date_start
            name = "[Inizio]Cron job per offerta Carrello id %s" % self.id
            self.start_cron_job = self.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.cart',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([self.id]),
                'numbercall': "1",

            })

    @api.one
    @api.constrains('offer_type', 'n', 'n_price')
    def _check_n_x_price(self):
        if self.offer_type == 3:
            if(self.n <= 0):
                raise ValidationError("n deve essere  > 0")
            if(self.n_price <= 0):
                raise ValidationError("il prezzo fisso deve essere  > 0")

    @api.one
    def turn_off(self):
        self.write({'active': False})
        for pl in self.products_list:
            pl.active = False

    @api.one
    def turn_on(self):
        if not self.active:
            for pl in self.env['netaddiction.specialoffer.offer_cart_line'].search([('offer_cart_id', '=', self.id), ('active', '=', False)]):
                if self.qty_limit_is_available:
                    pl.qty_limit = pl.product_qty_available_now if pl.product_qty_available_now > 0 else 0
                    pl.active = pl.product_qty_available_now > 0
                else:
                    pl.active = True
            self.write({'active': True})

    @api.model
    def create(self, values):
        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        e creo i cron
        """
        now = fields.Datetime.now()
        if (values['date_start'] and values['date_start'] < now):
            raise ValidationError("Data inizio offerta non può essere prima della data odierna")
        elif (values['date_end'] and values['date_end'] < now):
            raise ValidationError("Data fine offerta non può essere prima della data odierna")

        res = super(ShoppingCartOffer, self).create(values)
        nextcall = res.date_end
        name = "[Scadenza]Cron job per offerta CARRELLO id %s" % res.id
        res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
            'name': name,
            'user_id': SUPERUSER_ID,
            'model': 'netaddiction.specialoffer.cart',
            'function': 'turn_off',
            'nextcall': nextcall,
            'args': repr([res.id]),
            'numbercall': "1",
        })
        if res.date_start and res.date_start > now:
            res.active = False
            for pl in res.products_list:
                pl.active = False

            nextcall = res.date_start
            name = "[Inizio]Cron job per offerta CARRELLO id %s" % res.id
            res.start_cron_job = res.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.cart',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall': "1",

            })
        else:
            res.turn_on()

        return res

    @api.one
    def populate_products_from_expression(self):
        if self.expression_id:
            dom = self.expression_id.find_products_domain()
            ids = []
            to_add = []
            for pl in self.products_list:
                ids.append(pl.product_id.id)

            for prod in self.env['product.product'].search(dom):
                if(prod.id not in ids):
                    to_add.append(self.env['netaddiction.specialoffer.offer_cart_line'].create({'product_id': prod.id, 'offer_cart_id': self.id, 'qty_max_buyable': self.qty_max_buyable, 'qty_limit': self.qty_limit, 'offer_type': self.offer_type, 'priority': self.priority}))

    @api.multi
    def remove_products(self):
        # in caso serva di cancellare tutte le order line
        # for pl2 in self.env['netaddiction.specialoffer.offer_catalog_line'].search([("create_uid","=",1)]):
        #     pl2.unlink()
        for offer in self:
            for pl in offer.products_list:
                pl.unlink()

    @api.multi
    def modify_products(self):
        for pl in self.products_list:
            pl.qty_max_buyable = self.qty_max_buyable
            pl.qty_limit = self.qty_limit
            pl.offer_type = self.offer_type
            pl.priority = self.priority

    @api.multi
    def _compute_qty_selled(self):
        for offer in self:
            temp = 0.0
            for pl in offer.products_list:
                temp += pl.qty_selled

            # search for inactive offers
            offer.qty_selled = temp

    @api.one
    def unlink(self):
        self.turn_off()


class OfferCartLine(models.Model):

    _name = "netaddiction.specialoffer.offer_cart_line"
    _order = "priority"

    active = fields.Boolean(default=False,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_cart_id = fields.Many2one('netaddiction.specialoffer.cart', string='Offerta Carrello', index=True, copy=False, required=True)
    qty_max_buyable = fields.Integer(string='Quantità massima acquistabile', help="Quantità massima di prodotti acquistabili in un singolo ordine in questa offerta. 0 è illimitato", required=True)
    qty_limit = fields.Integer(string='Quantità limite', help="Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    offer_type = fields.Selection([(1, 'Bundle'), (2, 'n x m'), (3, 'n x prezzo'), (4, 'Spedizioni Gratis')], string='Tipo Offerta', default=2, required=True)
    priority = fields.Integer(string="priorità", default=0)
    qty_selled = fields.Float(string='Quantità venduta', default=0.0)
    company_id = fields.Many2one('res.company', string='Azienda', related='offer_cart_id.company_id', store=True)

    product_qty_available_now = fields.Integer(related="product_id.qty_available_now", store=False)

    @api.one
    @api.constrains('offer_cart_id')
    def _check_priority(self):
        self.priority = self.offer_cart_id[0].priority
        self.offer_type = self.offer_cart_id[0].offer_type
        self.qty_max_buyable = self.offer_cart_id[0].qty_max_buyable
        self.qty_limit = self.offer_cart_id[0].qty_limit

    @api.one
    @api.constrains('active')
    def _check_active_bundle(self):
        if self.offer_type == 1 and not self.active and self.offer_cart_id.active:
            self.offer_cart_id.active = False
            for pl in self.offer_cart_id.products_list:
                if pl.id != self.id:
                    pl.active = False


class BonusOffer(models.Model):
    _name = "netaddiction.specialoffer.bonus"

    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=True)
    author_id = fields.Many2one(comodel_name='res.users', string='Autore', required=True, default=lambda self: self.env.user.id)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env["res.company"].browse(1).id)
    only_one = fields.Boolean(string='Un solo Bonus a scelta', default=True)
    text = fields.Text("testo offerta")
    qty_selled = fields.Float(string='Quantità venduta', default=0.0)
    bonus_products_list = fields.One2many('netaddiction.specialoffer.bonus_offer_line', 'bonus_offer_id', string='Lista prodotti', domain=['|', ('active', '=', False), ('active', '=', True)])
    products_with_bonus_list = fields.One2many('netaddiction.specialoffer.product_with_bonus_offer_line', 'bonus_offer_id', string='Lista prodotti', domain=['|', ('active', '=', False), ('active', '=', True)])

    _sql_constraints = [
        ('name', 'unique(name)', 'Nome offerta deve essere unico!'),
    ]

    @api.one
    def unlink(self):
        self.active = False

    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active:
            for pl in self.bonus_products_list:
                pl.active = False
            for pl in self.products_with_bonus_list:
                pl.active = False

    @api.multi
    def apply_to_previous_orders(self):
        u"""Metodo per aggiungere i bonus dell'offerta negli ordini fatti prima della creazione dell'offerta.
        """
        for offer in self:
            if offer.active and not offer.only_one and offer.bonus_products_list and offer.products_with_bonus_list:
                # non funziona per le offerte a scelta
                id_list = [line.product_id.id for line in offer.products_with_bonus_list]
                id_bonus_list = [line.product_id.id for line in offer.bonus_products_list]
                picks = self.env["stock.picking"].search([("state", "not in", ("cancel", "done")), ("move_lines.product_id", "in", id_list)], order="date")
                if picks and id_bonus_list:
                    # prendo prodotti bonus e le location
                    bonus_prods = self.env["product.product"].search([("id", "in", id_bonus_list)])
                    location = self.env.ref('stock.stock_location_stock')
                    location_dest = self.env.ref('stock.stock_location_customers')
                    for pick in picks:
                        # controllo che questa pick non abbia già i bonus
                        already_have_bonus = [line for line in pick.move_lines if line.product_id.id in id_bonus_list]
                        if already_have_bonus:
                            continue
                        # se non li ha aggiungo move line e sale order line per ogni bonus
                        num = [line.product_uom_qty for line in pick.move_lines if line.product_id.id in id_list]
                        num = sum(num)
                        for prod in bonus_prods:
                            if prod.sale_ok:
                                data_pick = {
                                    "product_id": prod.id,
                                    "product_uom_qty": num,
                                    "product_uom": prod.uom_id.id,
                                    "picking_id": pick.id,
                                    "location_id": location.id,
                                    "location_dest_id": location_dest.id,
                                    "name": prod.name,
                                }
                                data_order_line = {
                                    "product_id": prod.id,
                                    "product_uom_qty": num,
                                    "product_uom": prod.uom_id.id,
                                    "order_id": pick.sale_id.id,
                                }
                                self.env["stock.move"].create(data_pick)
                                self.env["sale.order.line"].create(data_order_line)
                        # va chiamata per far scalare la quantità del bonus
                        pick.action_confirm()



class BonusOfferLine(models.Model):

    _name = "netaddiction.specialoffer.bonus_offer_line"

    active = fields.Boolean(default=True,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta", related='product_id.sale_ok', store=True)
    product_id = fields.Many2one('product.product', string='Product', change_default=True, ondelete='restrict', required=True)
    bonus_offer_id = fields.Many2one('netaddiction.specialoffer.bonus', string='Offerta Bonus', index=True, copy=False, required=True)
    company_id = fields.Many2one('res.company', string='Azienda', related='bonus_offer_id.company_id', store=True)

    @api.one
    @api.constrains('active')
    def _check_active(self):

        if not self.active:

            active_list = [bl for bl in self.bonus_offer_id.bonus_products_list if bl.active]

            if not active_list and self.bonus_offer_id.active:
                self.bonus_offer_id.active = False


class ProductWithBonusOfferLine(models.Model):

    _name = "netaddiction.specialoffer.product_with_bonus_offer_line"

    active = fields.Boolean(default=True,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', change_default=True, ondelete='restrict', required=True)
    bonus_offer_id = fields.Many2one('netaddiction.specialoffer.bonus', string='Offerta Bonus', index=True, copy=False, required=True)
    company_id = fields.Many2one('res.company', string='Azienda', related='bonus_offer_id.company_id', store=True)


class VoucherOffer(models.Model):

    _name = "netaddiction.specialoffer.voucher"

    name = fields.Char(string='Titolo', required=True)
    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=True)
    author_id = fields.Many2one(comodel_name='res.users', string='Autore', required=True, default=lambda self: self.env.user.id)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env["res.company"].browse(1).id)
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    date_start = fields.Datetime('Start Date', help="Data di inizio della offerta, se non impostata l'offerta comincia subito", required=False)
    date_end = fields.Datetime('End Date', help="Data di fine dell'offerta", required=True)
    qty_limit = fields.Integer(string='Quantità limite', help="Quantità limite di prodotti vendibili in questa offerta. 0 è illimitato", required=True)
    qty_selled = fields.Float(string='Quantità venduta', default=0.0)
    code = fields.Char(string='Codice Voucher', required=True)
    offer_type = fields.Selection([(1, 'Sconto Fisso'), (2, 'Percentuale'), (3, 'Spedizioni Gratis')], string='Tipo Offerta', default=1)
    fixed_discount = fields.Float(string="Sconto fisso")
    percent_discount = fields.Integer(string="Sconto Percentuale")
    one_user = fields.Boolean(string='Associa a un solo utente', default=False)
    associated_user = fields.Many2one(comodel_name='res.partner', string='Beneficiario', default=None)
    end_cron_job = fields.Integer()
    start_cron_job = fields.Integer()
    products_list = fields.One2many('netaddiction.specialoffer.offer_voucher_line', 'offer_voucher_id', string='Lista prodotti', domain=['|', ('active', '=', False), ('active', '=', True)])
    customers_list = fields.Many2many('res.partner', string="Clienti")

    _sql_constraints = [
        ('name', 'unique(name)', 'Nome offerta deve essere unico!'),
    ]

    @api.one
    @api.constrains('active')
    def _check_active(self):
        if not self.active:
            for pl in self.products_list:
                pl.active = False

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):

        if(self.date_start and self.date_start >= self.date_end):
            raise ValidationError("Data fine offerta non può essere prima della data di inizio offerta")
        for cron in self.env['ir.cron'].search([('id', '=', self.end_cron_job), ('active', '=', True)]):
            cron.nextcall = self.date_end
        found_cron = False
        for cron in self.env['ir.cron'].search([('id', '=', self.start_cron_job), ('active', '=', True)]):
            cron.nextcall = self.date_start
            found_cron = True
        if not found_cron and self.date_start:

            nextcall = self.date_start
            name = "[Inizio]Cron job per offerta Voucher id %s" % self.id
            self.start_cron_job = self.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.voucher',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([self.id]),
                'numbercall': "1",

            })

    @api.multi
    def write(self, values):
        if 'offer_type' in values:
            if values['offer_type'] == 1:
                values['percent_discount'] = 0.0
            elif values['offer_type'] == 2:
                values['fixed_discount'] = 0.0
        return super(VoucherOffer, self).write(values)

    @api.model
    def create(self, values):

        """
        quando  creo una offerta verifico anche che le date siano dopo la data corrente
        e creo i cron
        """
        now = fields.Date.today()
        if (values['date_start'] and values['date_start'] < now):
            raise ValidationError("Data inizio offerta non può essere prima della data odierna")
        elif (values['date_end'] and values['date_end'] < now):
            raise ValidationError("Data fine offerta non può essere prima della data odierna")

        res = super(VoucherOffer, self).create(values)
        nextcall = res.date_end
        name = "[Scadenza]Cron job per offerta VOUCHER id %s" % res.id
        res.end_cron_job = res.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
            'name': name,
            'user_id': SUPERUSER_ID,
            'model': 'netaddiction.specialoffer.voucher',
            'function': 'turn_off',
            'nextcall': nextcall,
            'args': repr([res.id]),
            'numbercall': "1",
        })
        if res.date_start and res.date_start > now:
            res.active = False
            for pl in res.products_list:
                pl.active = False

            nextcall = res.date_start
            name = "[Inizio]Cron job per offerta VOUCHER id %s" % res.id
            res.start_cron_job = res.pool.get('ir.cron').create(self.env.cr, self.env.uid, {
                'name': name,
                'user_id': SUPERUSER_ID,
                'model': 'netaddiction.specialoffer.voucher',
                'function': 'turn_on',
                'nextcall': nextcall,
                'args': repr([res.id]),
                'numbercall': "1",

            })
        else:
            res.turn_on()

        return res

    @api.one
    def populate_products_from_expression(self):
        if self.expression_id:
            dom = self.expression_id.find_products_domain()
            ids = []
            to_add = []
            for pl in self.products_list:
                ids.append(pl.product_id.id)

            for prod in self.env['product.product'].search(dom):
                if(prod.id not in ids):
                    to_add.append(self.env['netaddiction.specialoffer.offer_voucher_line'].create({'product_id': prod.id, 'offer_voucher_id': self.id, }))

    @api.multi
    def remove_products(self):
        # in caso serva di cancellare tutte le order line
        # for pl2 in self.env['netaddiction.specialoffer.offer_catalog_line'].search([("create_uid","=",1)]):
        #     pl2.unlink()
        for offer in self:
            for pl in offer.products_list:
                pl.unlink()

    # @api.multi
    # def modify_products(self):
    #     for pl in self.products_list:
    #         pl.qty_max_buyable = self.qty_max_buyable
    #         pl.offer_type = self.offer_type
    #         pl.percent_discount = self.percent_discount
    #         pl.fixed_discount = self.fixed_discount
    @api.one
    def turn_off(self):
        self.write({'active': False})
        for pl in self.products_list:
            pl.active = False

    @api.one
    def turn_on(self):
        for pl in self.env['netaddiction.specialoffer.offer_voucher_line'].search([('offer_voucher_id', '=', self.id), ('active', '=', False)]):
            pl.active = True
        self.write({'active': True})

    @api.one
    def unlink(self):
        self.turn_off()


class VoucherOfferLine(models.Model):

    _name = "netaddiction.specialoffer.offer_voucher_line"

    active = fields.Boolean(default=True,
        help="Spuntato = offerta attiva, Non Spuntato = offerta spenta")
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    offer_voucher_id = fields.Many2one('netaddiction.specialoffer.voucher', string='Offerta Voucher', index=True, copy=False, required=True)

    @api.one
    @api.constrains('fixed_price', 'offer_type')
    def _check_fixed_price(self):
        if self.offer_type == 1 and self.fixed_price <= 0:
            raise ValidationError("Il valore del prezzo fisso non può essere minore  o uguale di zero")

    @api.one
    @api.constrains('percent_discount', 'offer_type')
    def _check_percent_discount(self):
        if self.offer_type == 2 and (self.percent_discount <= 0 or self.percent_discount > 100):
            raise ValidationError("Il valore dello sconto percentuale non può essere minore di 0 o maggiore di 100")

class VoucherPartner(models.Model):
    _inherit = 'res.partner'

    vouchers_list = fields.Many2many('netaddiction.specialoffer.voucher', string="Voucher usati")
