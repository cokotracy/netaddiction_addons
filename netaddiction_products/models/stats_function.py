# -*- coding: utf-8 -*-

from openerp import models, api
class ProductsStats(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_shipped_in_interval_date(self, date_start, date_finish, supplier=False, count_refund=False):
        # ritorna la quantità, il numero degli ordini spediti[righe spedizione movimentate] nell'intervallo di tempo
        # supplier è opzionale [id del fornitore], se passato i valori sono corrispondenti solo ed esclusivamente a quel fornitore
        # count_refund: se true toglie i resi nel periodo, altrimenti se ne fotte
        customer_stock = self.env.ref('stock.stock_location_customers').id
        stock = self.env.ref('stock.stock_location_stock').id
        pids = []
        for product in self:
            pids.append(product.id)
        domain = [('date', '>=', date_start), ('date', '<=', date_finish), ('state', '=', 'done'),
            ('company_id', '=', self.env.user.company_id.id), ('product_id', 'in', pids), ('location_dest_id', '=', customer_stock), ('location_id', '=', stock)]
        if supplier:
            domain.append(('quant_ids.history_ids.picking_id.partner_id', '=', supplier))

        moves = self.env['stock.move'].read_group(domain=domain, fields=['product_id', 'product_uom_qty'], groupby=['product_id'])

        if count_refund:
            refund = self.get_refund_in_interval_date(date_start, date_finish, supplier)
            refs = {}
            for ref in refund:
                refs[ref['product_id'][0]] = {
                    'qty': ref['product_uom_qty'],
                    'product_id_count': ref['product_id_count']
                }

            for move in moves:
                if move['product_id'][0] in refs.keys():
                    move['product_uom_qty'] = move['product_uom_qty'] - refs[move['product_id'][0]]['qty']
                    move['product_id_count'] = move['product_id_count'] - refs[move['product_id'][0]]['product_id_count']

        return moves

    @api.multi
    def get_sale_in_interval_date(self, date_start, date_finish, supplier=False, count_refund=False, order_states=['done', 'partial_done', 'pending']):
        # ritorna la quantità, il valore, il numero degli ordini[numero linee ordine] venduti nell'intervallo di tempo
        # in result: product_uom_qty = quantità, price_total = valore, product_id_count = numero_ordini, product_id = (id prod, name prod)
        # count_refund: se true toglie i resi nel periodo, altrimenti se ne fotte
        # order_states sono gl istati da contare, per esempio in lavorazione per i preorder
        pids = []
        for product in self:
            pids.append(product.id)
        domain = [('order_id.date_order', '>=', date_start), ('order_id.date_order', '<=', date_finish), ('company_id', '=', self.env.user.company_id.id),
                ('product_id', 'in', pids), ('state', 'in', order_states)]
        if supplier:
            domain.append(('product_id.seller_ids.name', '=', supplier))
        result = self.env['sale.order.line'].read_group(domain=domain, fields=['product_id', 'product_uom_qty', 'price_total', 'qty_reverse'], groupby=['product_id'])

        if count_refund:
            refund = self.get_refund_in_interval_date(date_start, date_finish, supplier)
            refs = {}
            for ref in refund:
                refs[ref['product_id'][0]] = {
                    'qta': ref['product_uom_qty'],
                    'product_id_count': ref['product_id_count']
                }
            for move in result:
                if move['product_id'][0] in refs.keys():
                    move['product_uom_qty'] = move['product_uom_qty'] - refs[move['product_id'][0]]['qta']
                    move['product_id_count'] = move['product_id_count'] - refs[move['product_id'][0]]['product_id_count']

        return result

    @api.multi
    def get_refund_in_interval_date(self, date_start, date_finish, supplier=False):
        # ritorna la quantità di resi
        customer_stock = self.env.ref('stock.stock_location_customers').id
        stock = self.env.ref('stock.stock_location_stock').id
        difettati = self.env['stock.location'].search([('name', 'ilike', 'Difettati')]).id
        pids = []
        for product in self:
            pids.append(product.id)
        domain = [('date', '>=', date_start), ('date', '<=', date_finish), ('state', '=', 'done'),
            ('company_id', '=', self.env.user.company_id.id), ('product_id', 'in', pids), ('location_id', '=', customer_stock), ('location_dest_id', 'in', [stock, difettati])]
        if supplier:
            domain.append(('quant_ids.history_ids.picking_id.partner_id', '=', supplier))

        moves = self.env['stock.move'].read_group(domain=domain, fields=['product_id', 'product_uom_qty'], groupby=['product_id'])

        return moves
