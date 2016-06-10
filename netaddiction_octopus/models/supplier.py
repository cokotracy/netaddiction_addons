from openerp import api, models, fields

from ..base.registry import registry


class Supplier(models.Model):
    _name = 'netaddiction_octopus.supplier'
    _inherits = {'res.partner': 'partner_id'}
    _order = 'order'

    handler = fields.Selection([(handler, handler) for handler in registry.suppliers], string='Handler')
    order = fields.Integer('Ordine')
    category_ids = fields.One2many('netaddiction_octopus.category', 'supplier_id')

    @api.multi
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
            },
        }
