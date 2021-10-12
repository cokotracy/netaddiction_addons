# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def write(self, values):
        res = super().write(values)
        # If a picking linked to an order it's in a pickup,
        # it's possible only to write the state in `cancel`
        if self.env.context.get('ignore_pickup_check'):
            return res
        if values.get('state', '') == 'cancel' and len(values.keys()) == 1:
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

    # TODO: Remove `problem` state
    # **Warning**
    # `problem` state can't be deleted because there are old orders
    # in this state. We will remove it when them change state.
    state = fields.Selection(selection_add=[
        ('sale', 'In Lavorazione'),
        ('problem', 'Problema'),
    ])

    problem = fields.Boolean()

    is_in_a_pickup = fields.Boolean(
        compute='_compute_is_in_a_pickup',
        store=True,
    )

    def write(self, values):
        # When a note is set on the order (f.e. from the ecommerce)
        # the order pass to state problem to highlight that it need attention
        if values.get('note', '').strip():
            values['problem'] = True
        res = super().write(values)
        # If a picking linked to an order it's in a pickup,
        # it's possible only to write
        # the state in `cancel` or sale with a problem
        if self.env.context.get('ignore_pickup_check'):
            return res
        if ('problem' in values or values.get('state', '') == 'cancel') \
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

    def action_problems(self):
        # Migrated from netaddiction_mail/models/sale v9.0
        # Set order to `problem`
        for order in self:
            order.problem = True

    def action_remove_problems(self):
        message_model = self.env['mail.message']
        subtype = self.env.ref('mail.mt_note')
        for order in self:
            order.problem = False
            message_model.create({
                    'subject': 'Problema risolto',
                    'message_type': 'notification',
                    'model': 'sale.order',
                    'res_id': order.id,
                    'body':
                    f'Problema sull\'ordine risolto da {self.env.user.name}',
                    'subtype_id': subtype.id
                })

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
