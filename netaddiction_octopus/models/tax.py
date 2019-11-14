from odoo import api, models, fields
from ..base import registry


class Tax(models.Model):

    _name = 'netaddiction_octopus.tax'
    _order = 'field'

    code = fields.Char(
        'Codice',
        index=True,
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Azienda',
        related='supplier_id.partner_id.company_id',
        store=True
    )

    field = fields.Selection(
        '_get_field_selection',
        string='Campo',
        required=True
    )

    purchase_tax_id = fields.Many2one(
        'account.tax',
        string='Tassa di acquisto'
    )

    sale_tax_id = fields.Many2one(
        'account.tax',
        string='Tassa di vendita'
    )

    supplier_id = fields.Many2one(
        'netaddiction_octopus.supplier',
        string='Fornitore',
        required=True
        )

    @api.onchange('supplier_id')
    def _get_field_selection(self):
        if 'active_id' not in self.env.context:
            return []
        supplier = self.env['netaddiction_octopus.supplier'].search(
            [('id', '=', self.env.context['active_id'])])
        options = []
        imported_module = registry.custom_supplier_module(supplier.handler)
        handler = imported_module.CustomSupplier()
        for f in handler.files:
            options.append(('[file] %s' % f['name'], f['name']))
            for field in handler.categories:
                label = '%s: %s' % (f['name'], field)
                options.append(('[field] %s' % label, label))
        return options
