# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sale_b2b_ko = fields.Boolean(
        string="Escludi dal B2B",
    )


class Products(models.Model):

    _inherit = 'product.product'

    b2b_price = fields.Char(
        compute='_compute_b2b_price',
        string="B2B Price",
    )

    def _compute_b2b_price(self):
        item_model = self.env['product.pricelist.item'].sudo()
        for product in self:
            result = item_model.search([
                ('product_id', '=', product.id),
                ('pricelist_id.is_b2b', '=', True),
                ])
            if result:
                texts = []
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
                    currency = res.pricelist_id.currency_id.symbol
                    texts.append(
                        f'{res.pricelist_id.name}: '
                        f'{b2b_noiva:.2f} {currency} '
                        f'[{b2b_iva:.2f} {currency}]', )
            else:
                texts = ['** NO B2B PRICELIST **']
            product.b2b_price = '; '.join(texts)
