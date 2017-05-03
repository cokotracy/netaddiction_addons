# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import Warning
from collections import defaultdict

class GrouponPickup(models.Model):
    _name = 'groupon.pickup.wave'

    name = fields.Char(string="Nome")
    order_ids = fields.One2many(comodel_name='netaddiction.groupon.sale.order', string='Ordini', inverse_name="wave_id")
    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('done', 'Completato'),
    ], string='Stato', readonly=True, default="draft")
    date_close = fields.Datetime(string="Data Chiusura")

    @api.one
    def unlink(self):
        if self.state != 'draft':
            return super(GrouponPickup, self).unlink()

        raise Warning("Non puoi cancellare una lista prelievo completata.")

    @api.model
    def create_wave(self):
        orders = self.env['netaddiction.groupon.sale.order'].search([('state', '=', 'draft'), ('picking_ids', '!=', False), ('wave_id', '=', False)])

        if len(orders) > 0:
            attr = {
                'order_ids': [(6, False, orders.mapped('id'))],
            }
            wave = self.create(attr)
            wave.name = 'Lista Groupon %s' % (wave.id)

            return 'ok'
        else:
            return 'Non ci sono ordini da pickuppare.'

    @api.multi
    def get_list_products(self):
        self.ensure_one()
        qtys = defaultdict(lambda: defaultdict(float))
        products = {}
        for order in self.order_ids:
            for picks in order.picking_ids:
                for pick in picks.pack_operation_product_ids:
                    qtys[pick.product_id.barcode]['product_qty'] += pick.product_qty
                    qtys[pick.product_id.barcode]['remaining_qty'] += pick.remaining_qty
                    qtys[pick.product_id.barcode]['qty_done'] += pick.qty_done
                products[pick.product_id] = qtys[pick.product_id.barcode]

        return products

    @api.model
    def get_groupon_shelf_to_pick(self, product, qty):
        shelf = {}
        for alloc in product.groupon_wh_location_line_ids:
            if qty > 0:
                if qty <= alloc.qty:
                    shelf[alloc.wh_location_id] = int(qty)
                    qty = 0
                else:
                    shelf[alloc.wh_location_id] = int(alloc.qty)
                    qty = int(qty) - int(alloc.qty)

        return shelf
