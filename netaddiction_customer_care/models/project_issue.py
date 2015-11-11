# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Issue(models.Model):
    _inherit = 'project.issue'

    order_id = fields.Many2one('sale.order',ondelete="restrict",
        string="Ordine")

class OrderIssue(models.Model):
    _inherit = 'sale.order'

    issue_id = fields.One2many('project.issue','order_id')
