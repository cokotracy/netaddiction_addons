from odoo import api, models


class Supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.onchange('name')
    def search_timing(self):
        self.delay = self.name.supplier_delivery_time
