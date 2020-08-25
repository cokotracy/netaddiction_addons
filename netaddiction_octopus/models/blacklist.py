from odoo import models, fields


class Blacklist(models.Model):
    _name = 'netaddiction_octopus.blacklist'
    _description = 'Octopus Blacklist'

    _sql_constraints = [(
        'duplicate',
        'unique(supplier_id, supplier_code)',
        'This product is already blacklisted')]

    supplier_code = fields.Char(
        string='Codice fornitore'
    )

    supplier_id = fields.Many2one(
        'res.partner',
        string='Fornitore',
        domain=[('supplier', '=', True)]
    )
