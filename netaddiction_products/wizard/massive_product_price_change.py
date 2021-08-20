# Copyright 2021 Rapsodoo (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class MassiveProductPriceChange(models.TransientModel):

    _name = 'massive.product.price.change'
    _description = 'Massive change for product price from template'

    def _default_template_ids(self):
        template_ids = self.env.context.get('active_ids', [])
        return [(4, tid) for tid in template_ids]

    template_ids = fields.Many2many(
        'product.template',
        string='Templates',
        default=_default_template_ids,
        )

    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        )

    line_ids = fields.One2many(
        'massive.product.price.change.line',
        'wizard_id',
        # default=_default_line_ids,
        string='Lines')

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        lines = [(5, ), ]
        template_ids = self.env.context.get('active_ids', [])
        if template_ids and self.pricelist_id:
            products = self.env['product.product'].search(
                [('product_tmpl_id', 'in', template_ids)])
            pricelist = self.pricelist_id
            items = pricelist.item_ids.filtered(
                lambda i: (i.product_id and i.product_id.id in products.ids))
            for item in items:
                product = item.product_id
                lines.append((0, 0, {
                    'item_id': item.id,
                    'product_id': product.id,
                    'sale_price': item.fixed_price,
                    'can_be_deleted': True,
                    }), )
        self.line_ids = lines

    def apply_price(self):
        # Apply changes only if price changes
        item_model = self.env['product.pricelist.item']
        for line in self.line_ids.filtered(lambda l: l.state != 'none'):
            # If it's a new line, create an item in the pricelist
            if line.state == 'new':
                item_model.create({
                    'pricelist_id': self.pricelist_id.id,
                    'applied_on': '0_product_variant',
                    'product_id': line.product_id.id,
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'fixed_price': line.sale_price,
                    })
            # If there is a change, register it on existing item
            elif line.state == 'change':
                line.item_id.fixed_price = line.sale_price
            elif line.state == 'delete':
                line.item_id.unlink()
        return True


class MassiveProductPriceChangeLine(models.TransientModel):

    _name = 'massive.product.price.change.line'
    _description = 'Massive change for product price from template - Detail'

    wizard_id = fields.Many2one(
        'massive.product.price.change',
        string='wizard',
        )

    item_id = fields.Many2one(
        'product.pricelist.item',
        string='Pricelist Line',
        )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        )

    sale_price = fields.Float()

    state = fields.Selection([
        ('none', 'None'),
        ('change', 'Change'),
        ('new', 'New'),
        ('delete', 'Delete'),
        ], default='none')

    can_be_deleted = fields.Boolean()

    to_delete = fields.Boolean()

    template_ids = fields.Many2many(
        'product.template',
        string='Templates',
        related='wizard_id.template_ids',
        )

    @api.onchange('sale_price', 'to_delete')
    def onchange_sale_price(self):
        for line in self:
            if line.to_delete:
                line.state = 'delete'
            elif not line.item_id:
                line.state = 'new'
            elif line.item_id and (
                    line.sale_price != line.item_id.fixed_price):
                line.state = 'change'
            else:
                line.state = 'none'
