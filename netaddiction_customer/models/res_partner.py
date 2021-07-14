from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    street2 = fields.Char(
        string='Civico'
    )
