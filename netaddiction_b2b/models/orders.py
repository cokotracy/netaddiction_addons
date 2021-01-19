# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Orders(models.Model):
    _inherit = 'sale.order'

    is_b2b = fields.Boolean(
        string="B2B"
    )
