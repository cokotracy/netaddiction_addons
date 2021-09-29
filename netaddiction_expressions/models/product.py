# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    out_date = fields.Date()
