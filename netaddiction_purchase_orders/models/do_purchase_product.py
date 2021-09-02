# -*- coding: utf-8 -*-

from odoo import models, api, fields


class DoPurchaseProducts(models.TransientModel):
    _name = "do.purchase.product"
    _description = "Do Purchase Product"

    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    qty = fields.Integer(string="Quantità", default=1)
    supplier = fields.Selection(string="Fornitore", selection="_get_selection")

    @api.model
    def default_get(self, fields):
        attr = {
            'product_id': self.env.context.get('this_product', False),
            'qty': 1
        }
        return attr

    @api.model
    def _get_selection(self):
        return self.env.context.get('selection', [])

    def do_put_in_purhcase_order(self):
        products = [[self.product_id.id, self.supplier, self.qty], ]
        order = self.env['purchase.order'].put_in_order(products)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'target': 'curent',
            'res_id': order.id,
            }


class ProductProduct(models.Model):
    _inherit = "product.product"

    def open_do_purchase(self):
        self.ensure_one()
        select = []
        for seller in self.seller_ids:
            text = '%s - %s' % (seller.name.name, seller.price)
            select.append((seller.name.id, text))
        action = self.env.ref(
            'netaddiction_purchase_orders.'
            'netaddiction_do_purchase_product_action').read()[0]
        ctx = self.env.context.copy()
        ctx.update({
                'this_product': self.id,
                'selection': select
            })
        action['context'] = ctx
        return action
