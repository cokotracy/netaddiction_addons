# Copyright 2019-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


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
        ('partial_done', 'Parzialmente Completato'),
        ('problem', 'Problema'),
        # ('done', 'Completato'),
        # ('cancel', 'Annullato'),
        # ('pending', 'Pendente'),
    ])

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
