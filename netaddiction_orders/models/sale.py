# Copyright 2019-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def write(self, values):
        res = super().write(values)
        # If a picking linked to an order it's in a pickup,
        # it's possible only to write the state in `problem` or `cancel`
        if self.env.context.get('ignore_pickup_check'):
            return res
        if values.get('state', '') in ('problem', 'cancel') \
                and len(values.keys()) == 1:
            return res
        for sale in self.mapped('order_id'):
            if sale.is_in_a_pickup:
                raise ValidationError(
                    _('Impossibile to change values for orders in a pickup')
                    )
        return res

    @api.depends('product_id', 'order_id.state', 'qty_invoiced',
                 'qty_delivered')
    def _compute_product_updatable(self):
        super()._compute_product_updatable()
        # https://youtu.be/lDqlasyMJog?t=2
        for line in self:
            line.product_updatable = True

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super().product_uom_change()
        if getattr(self, '_origin', None):
            self.price_unit = \
                self._origin.read(["price_unit"])[0]["price_unit"]


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    customer_comment = fields.Text()

    child_orders = fields.One2many(
        'sale.order', 'parent_order', string='Child Orders')

    created_by_the_customer = fields.Boolean(
        string="Created By Customer",
    )

    ip_address = fields.Char()

    parent_order = fields.Many2one(
        'sale.order',
        string="Parent Order",
        ondelete='set null'
    )

    pronto_campaign = fields.Boolean(
        string="Prontocampaign order"
    )

    state = fields.Selection(selection_add=[
        # ('draft', 'Nuovo'),
        # ('sent', 'Preventivo Inviato'),
        ('sale', 'In Lavorazione'),
        ('problem', 'Problema'),
        # ('done', 'Completato'),
        # ('cancel', 'Annullato'),
        # ('pending', 'Pendente'),
    ])

    is_in_a_pickup = fields.Boolean(
        compute='_compute_is_in_a_pickup',
        store=True,
    )

    def write(self, values):
        res = super().write(values)
        # If a picking linked to an order it's in a pickup,
        # it's possible only to write the state in `problem` or `cancel`
        if self.env.context.get('ignore_pickup_check'):
            return res
        if values.get('state', '') in ('problem', 'cancel') \
                and len(values.keys()) == 1:
            return res
        for sale in self:
            if sale.is_in_a_pickup:
                raise ValidationError(
                    _('Impossibile to change values for orders in a pickup')
                    )
        return res

    @api.depends('picking_ids', 'picking_ids.batch_id')
    def _compute_is_in_a_pickup(self):
        for sale in self:
            pickings_with_batch = \
                sale.mapped('picking_ids').filtered(lambda p: p.batch_id)
            sale.is_in_a_pickup = True if pickings_with_batch else False

    # Super to fix a problem in `odoo_website_wallet` module >:(
    def _get_invoiced(self):
        return super(
            SaleOrder,
            self.with_context(ignore_pickup_check=True)
        )._get_invoiced()

    '''

    Functions based on old logics.
    We keep them, for now.

    def _check_offers_catalog(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        """controlla le offerte catalogo e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit
        per la sua offerta catalogo corrispondente
        False altrimenti
        """
        self.ensure_one()
        problems = False
        if self.state != 'draft':
            return problems
        for line in self.order_line:
            if line.offer_type and not line.negate_offer:
                offer_line = line.product_id.offer_catalog_lines[0] \
                    if len(line.product_id.offer_catalog_lines) > 0 \
                    else None
                if offer_line:
                    offer_line.qty_selled += line.product_uom_qty
                    offer_line.active = offer_line.qty_limit == 0 \
                        or offer_line.qty_selled < offer_line.qty_limit
                    if offer_line.qty_limit > 0 \
                            and offer_line.qty_selled > offer_line.qty_limit:
                        attr = {
                            'subtype': "mt_comment",
                            'res_id': self.id,
                            'model': 'sale.order',
                            'author_id': self.env.user.partner_id.id,
                            'message_type': 'comment',
                            'body': 'in problema perché superato il qty '
                            'limit per offerta: %s, '
                            'prodotto: %s, '
                            'quantità ordinata: %s, '
                            'quantità che era disponibile in offerta: %s' % (
                                offer_line.offer_catalog_id.name,
                                line.product_id.name,
                                line.product_uom_qty,
                                (offer_line.qty_limit - (offer_line.qty_selled)
                                )),
                            }
                        self.env['mail.message'].create(attr)
                        problems = True
                else:
                    attr = {
                        'subtype': "mt_comment",
                        'res_id': self.id,
                        'body': 'in problema perché offerta scaduta, '
                        'prodotto: %s' % (line.product_id.name),
                        'model': 'sale.order',
                        'author_id': self.env.user.partner_id.id,
                        'message_type': 'comment',
                    }
                    self.env['mail.message'].create(attr)
                    problems = True
        return problems

    def _check_offers_cart(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        """controlla le offerte carrello e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit
        per la sua offerta carrello corrispondente
        False altrimenti
        """
        self.ensure_one()
        problems = False
        if self.state != 'draft':
            return problems
        for och in self.offers_cart:
            offer_line = och.offer_cart_line
            if offer_line:
                offer_line.qty_selled += och.qty
                offer_line.active = offer_line.qty_limit == 0 \
                    or offer_line.qty_selled < offer_line.qty_limit
                if offer_line.qty_limit > 0 and \
                        offer_line.qty_selled > offer_line.qty_limit:
                    attr = {
                        'subtype': "mt_comment",
                        'res_id': self.id,
                        'body': 'in problema perché superato '
                        'il qty limit per offerta: %s, '
                        'prodotto: %s, '
                        'quantità ordinata: %s, '
                        'quantità che era disponibile in offerta: %s' % (
                            offer_line.offer_catalog_id.name,
                            offer_line.order_line.product_id.name,
                            offer_line.order_line.product_uom_qty,
                            (offer_line.qty_limit - (
                                offer_line.qty_selled -
                                offer_line.order_line.product_uom_qty))),
                        'model': 'sale.order',
                        'author_id': self.env.user.partner_id.id,
                        'message_type': 'comment',
                    }
                    self.env['mail.message'].create(attr)
                    problems = True
            else:
                attr = {
                    'subtype': "mt_comment",
                    'res_id': self.id,
                    'body': 'in problema perché offerta non trovata per '
                    'offer cart history: %s, '
                    'prodotto: %s, '
                    'quantità ordinata: %s' % (
                        och.id, och.product_id.name, och.qty),
                    'model': 'sale.order',
                    'author_id': self.env.user.partner_id.id,
                    'message_type': 'comment',
                }
                self.env['mail.message'].create(attr)
                problems = True
        return problems

    def _check_offers_voucher(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        """controlla le offerte voucher e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit
        per la sua offerta carrello corrispondente
        False altrimenti
        """
        self.ensure_one()
        problems = False
        if self.state != 'draft':
            return problems
        for ovh in self.offers_voucher:
            offer = ovh.offer_id
            if offer:
                offer.qty_selled += ovh.qty
                offer.active = offer.qty_limit == 0 or \
                    offer.qty_selled < offer.qty_limit
            if offer and offer.qty_limit > 0 and \
                    offer.qty_selled > offer.qty_limit:
                attr = {
                    'subtype': "mt_comment",
                    'res_id': self.id,
                    'body': 'in problema perché superato il qty limit '
                    'per offerta: %s, '
                    'prodotto: %s, '
                    'quantità ordinata: %s, '
                    'quantità che era disponibile in offerta: %s' % (
                        offer.name,
                        ovh.order_line.product_id.name,
                        ovh.order_line.product_uom_qty, (
                            offer.qty_limit - (
                                offer.qty_selled -
                                ovh.order_line.product_uom_qty))),
                    'model': 'sale.order',
                    'author_id': self.env.user.partner_id.id,
                    'message_type': 'comment',
                }
                self.env['mail.message'].create(attr)
                problems = True
        return problems

    def _check_digital_bonus(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        self.ensure_one()
        if self.state != 'draft':
            return
        for line in self.order_line:
            # per tutte le order line..
            for bonus_offer in line.product_id.code_ids:
                # per ogni offerta digitale del prodotto..
                if not bonus_offer.assign_codes or (
                        bonus_offer.qty_limit > 0
                        and bonus_offer.qty_sold >= bonus_offer.qty_limit):
                    # se l'offerta è esaurita o non ha codici
                    # passo alla prossima
                    continue
                codes = self.env["netaddiction.specialoffer.digital_code"]\
                    .search([("bonus_id", "=", bonus_offer.id),
                             ("sent", "=", False),
                             ("order_id", "=", None)])
                if len(codes) > 0:
                    # ci sono i codici, li assegno
                    i = 0
                    while i < line.product_uom_qty and i < len(codes):
                        code = codes[i]
                        code.order_id = self.id
                        code.order_line_id = line.id
                        i += 1
                    bonus_offer.qty_sold += i
                else:
                    # non ci sono i codici loggo
                    # (comunque potrebbero essere assegnati in seguito)
                    attr = {
                        'subtype': "mt_comment",
                        'res_id': self.id,
                        'body': 'non è stato assegnato nessun bonus '
                        'digitale per il prodotto %s' % line.product_id.name,
                        'model': 'sale.order',
                        'author_id': self.env.user.partner_id.id,
                        'message_type': 'comment',
                    }
                    self.env['mail.message'].create(attr)
                    bonus_offer.qty_sold += line.product_uom_qty
    '''

    def action_problems(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        # Set state to `problem`
        for order in self:
            # order._check_offers_catalog()
            # order._check_offers_cart()
            # order._check_offers_voucher()
            # order._check_digital_bonus()
            order.state = 'problem'
            order.order_line.state = 'problem'

    def action_cancel(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        # Send an internal mail for cancel order with paypal or sofort payment
        # to refund the payment to user
        paypal_journal = self.env.ref('netaddiction_payments.paypal_journal')
        sofort_journal = self.env.ref('netaddiction_payments.sofort_journal')
        journals = (paypal_journal.id, sofort_journal.id)
        states = ('draft', 'done', 'pending')
        user = self.env.user
        template = self.env.ref(
            'netaddiction_orders.refund_payment_cancel_sale')
        template = template.sudo().with_context(lang=user.lang)
        for sale in self:
            if sale.created_by_the_customer and \
                    sale.state not in states and \
                    sale.payment_method_id.id in journals:
                template.send_mail(
                    sale.id, force_send=False, raise_exception=True)
        return super().action_cancel()

    def action_confirm(self):
        problem_orders = self.filtered(lambda o: o.state == 'problem')
        res = super().action_confirm()
        # keep state `problem` on orders with this state
        if not self.env.context.get('confirm_problem_order', False):
            problem_orders.state = 'problem'
        return res

    def action_confirm_problem(self):
        ctx = dict(self.env.context or [])
        ctx['confirm_problem_order'] = True
        res = self.with_context(ctx).action_confirm()
        return res
