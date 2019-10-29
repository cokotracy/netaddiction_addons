# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
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
