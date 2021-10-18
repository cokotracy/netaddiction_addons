from odoo import api, models


class Supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.onchange('name')
    def search_timing(self):
        self.delay = self.name.supplier_delivery_time

    @api.model
    def create(self, values):
        # Migrated from 9.0:
        # netaddiction_products/models/products.py - SupplierInfo - create
        # Get delay from supplier if not defined
        if values.get('delay') is None:
            supplier = self.env['res.partner'].browse(values['name'])
            values['delay'] = supplier.supplier_delivery_time
        return super().create(values)
