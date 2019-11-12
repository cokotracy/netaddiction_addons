from openerp import api, models, fields

from ..base.registry import registry


class Category(models.Model):
    _name = 'netaddiction_octopus.category'
    _order = 'field, type desc'

    supplier_id = fields.Many2one('netaddiction_octopus.supplier', string='Fornitore', required=True)
    field = fields.Selection('_get_field_selection', string='Campo', required=True)
    code = fields.Char('Codice', index=True, required=True)
    type = fields.Selection([('category', 'Categoria'), ('attribute', 'Attributo'), ('trash', 'Scarta')],
        string='Tipo', required=True)
    category_id = fields.Many2one('product.category', string='Categoria')
    attribute_id = fields.Many2one('product.attribute.value', string='Attributo')
    company_id = fields.Many2one('res.company', string='Azienda',
        related='supplier_id.partner_id.company_id', store=True)

    @api.onchange('supplier_id')
    def _get_field_selection(self):
        if 'active_id' not in self.env.context:
            return []

        supplier = self.env['netaddiction_octopus.supplier'].search([('id', '=', self.env.context['active_id'])])

        options = []

        for handler in registry:
            if handler.__name__ != supplier.handler:
                continue

            for f in handler.files:
                options.append(('[file] %s' % f['name'], f['name']))

                for field in handler.categories:
                    label = '%s: %s' % (f['name'], field)
                    options.append(('[field] %s' % label, label))

        return options
