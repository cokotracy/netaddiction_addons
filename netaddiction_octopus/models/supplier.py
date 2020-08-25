# -*- coding: utf-8 -*-

from odoo import models, fields


class Supplier(models.Model):
    _name = 'netaddiction_octopus.supplier'
    _description = 'Octopus Supplier'
    _inherits = {'res.partner': 'partner_id'}
    _order = 'order'

    can_add = fields.Boolean(
        string='Può aggiungere',
        default=False
    )

    category_ids = fields.One2many(
        'netaddiction_octopus.category',
        'supplier_id',
        string='Categories'
    )

    handler = fields.Selection([
        ('adl', 'adl'),
        ('beegroup', 'beegroup'),
        ('cidiverte', 'cidiverte'),
        ('cosmicgroup', 'cosmicgroup'),
        ('dbline', 'dbline'),
        ('drako', 'drako'),
        ('esprinet', 'esprinet'),
        ('gedistribuzione', 'gedistribuzione'),
        ('promovideo', 'promovideo'),
        ('terminalvideo', 'terminalvideo'),
        ],
        string='Handler'
    )

    order = fields.Integer(
        string='Ordine'
    )

    tax_ids = fields.One2many(
        'netaddiction_octopus.tax',
        'supplier_id',
        string='Taxes'
    )

    def manage_categories(self):
        self.ensure_one()
        return {
            'name': 'Gestione categorie %s' % self.handler,
            'view_type': 'form',
            'view_mode': 'list',
            'view_id': False,
            'res_model': 'netaddiction_octopus.category',
            'type': 'ir.actions.act_window',
            'domain': [('supplier_id.id', '=', self.id)],
            'target': 'new',
            'flags': {
                'action_buttons': True,
                'pager': True,
            },
            'context': {
                'default_supplier_id': self.id,
                'handler': self.handler,
                'company_id': self.partner_id.company_id.id,
            },
        }

    def manage_taxes(self):
        self.ensure_one()
        return {
            'name': 'Gestione tasse %s' % self.handler,
            'view_type': 'form',
            'view_mode': 'list',
            'view_id': False,
            'res_model': 'netaddiction_octopus.tax',
            'type': 'ir.actions.act_window',
            'domain': [('supplier_id.id', '=', self.id)],
            'target': 'new',
            'flags': {
                'action_buttons': True,
                'pager': True,
            },
            'context': {
                'default_supplier_id': self.id,
                'handler': self.handler,
                'company_id': self.partner_id.company_id.id,
            },
        }
