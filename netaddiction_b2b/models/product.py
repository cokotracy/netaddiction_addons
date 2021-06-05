# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class Products(models.Model):

    _inherit = 'product.product'

    b2b_price = fields.Char(
        compute='_compute_b2b_price',
        string="B2B Price",
    )

    def _compute_b2b_price(self):
        item_model = self.env['product.pricelist.item'].sudo()
        for product in self:
            text = ''
            result = item_model.search(
                [('product_id', '=', product.id)])
            if result:
                for res in result:
                    if res.pricelist_id.id:
                        price = res.pricelist_id.sudo().price_rule_get(
                            product.id, 1)
                        b2b = product.taxes_id.compute_all(
                            price[res.pricelist_id.id][0])
                    else:
                        b2b = product.taxes_id.compute_all(product.final_price)
                    b2b_iva = b2b['total_included']
                    b2b_noiva = b2b['total_excluded']
                    text += '%s - %s [%s]; ' % (
                        res.pricelist_id.name,
                        str(round(b2b_noiva, 2)).replace('.', ','),
                        str(round(b2b_iva, 2)).replace('.', ','))
            product.b2b_price = text
