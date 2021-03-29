# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime,date,timedelta
import collections
import io
import csv
import base64


class Suppliers(models.Model):

    _inherit = "res.partner"

    send_report = fields.Boolean(
        string="Il fornitore riceve i report del lunedì"
    )

    send_contact_report = fields.Boolean(
        string="Il contatto riceve i report del lunedì"
    )

    send_contact_purchase_orders = fields.Boolean(
        string="Il contatto riceve gli ordini di acquisto"
    )

    send_contact_purchase_orders_type = fields.Selection(
        [('none', 'None'), ('terminalvideo', 'Terminalvideo')],
        default='none',
        string='Il contatto riceve l\'allegato negli ordini di acquisto'
    )

    send_contact_refund = fields.Boolean(
        string="Il contatto riceve i resi"
    )


    @api.model
    def get_all_suppliers(self):
        result = self.search([
            ('supplier', '=', True),
            ('active', '=', True),
            ('parent_id', '=', False)
        ])
        supplier = []
        for res in result:
            supplier.append({'id': res.id, 'name': res.name})
        return supplier

    def generate_monday_report(self):
        self.ensure_one()
        if self.supplier_rank and len(self.parent_id) == 0:
            products_preorder = self.get_products_in_preorder()
            # devo recuperare i prodotti spediti che non stanno più in stock
            date_start = date.today() - timedelta(days=7)
            today = date.today()
            product_model = self.env['product.product']

            prods = []
            products = {}
            shipped_products = self.get_products_shipped(
                date_start.strftime('%Y-%m-%d 00:00:00'),
                today.strftime('%Y-%m-%d 23:59:59'),
                count_refund=True
            )
            for shipped in shipped_products:
                prods.append(shipped['product_id'][0])
                products[shipped['product_id'][0]] = {
                    'object': product_model.browse(
                        shipped['product_id'][0]
                    ),
                    'name': shipped['product_id'][1],
                    'qty_week': shipped['product_uom_qty'],
                    'qty_mag': 0,
                    'qty_all': 0
                }
            p_a = product_model.search([
                ('id', 'in', prods)
            ])
            moves = p_a.get_shipped_in_interval_date(
                '1999-01-01',
                today.strftime('%Y-%m-%d 23:59:59'),
                supplier=self.id,
                count_refund=True)
            for move in moves:
                if move['product_id'][0] in products:
                    products[move['product_id'][0]]['qty_all'] = \
                        move['product_uom_qty']

            products_stock = self.get_products_in_stock()
            pids_stock = []
            for stock in products_stock:
                pids_stock.append(stock['product_id'][0])
            ps = product_model.search([
                ('id', 'in', pids_stock)
            ])
            stock_moves_all = ps.get_shipped_in_interval_date(
                '1999-01-01',
                today.strftime('%Y-%m-%d 23:59:59'),
                supplier=self.id,
                count_refund=True
            )
            stock_moves_week = ps.get_shipped_in_interval_date(
                date_start.strftime('%Y-%m-%d 00:00:00'),
                today.strftime('%Y-%m-%d 23:59:59'),
                supplier=self.id,
                count_refund=True
            )
            for stock_move in stock_moves_week:
                if stock_move['product_id'][0] not in products:
                    products[stock_move['product_id'][0]] = {
                        'object': product_model.browse(
                            stock_move['product_id'][0]
                        ),
                        'name': stock_move['product_id'][1],
                        'qty_week': stock_move['product_uom_qty'],
                        'qty_mag': 0,
                        'qty_all': 0
                    }
            for stock_move in stock_moves_all:
                if stock_move['product_id'][0] in products:
                    products[stock_move['product_id'][0]]['qty_all'] = \
                        stock_move['product_uom_qty']
                else:
                    products[stock_move['product_id'][0]] = {
                        'object': product_model.browse(
                            stock_move['product_id'][0]
                        ),
                        'name': stock_move['product_id'][1],
                        'qty_week': 0,
                        'qty_mag': 0,
                        'qty_all': stock_move['product_uom_qty']
                    }

            for stock in products_stock:
                if stock['product_id'][0] in products:
                    products[stock['product_id'][0]]['qty_mag'] = \
                        stock['quantity']
                else:
                    products[stock['product_id'][0]] = {
                        'object': product_model.browse(
                            stock['product_id'][0]
                        ),
                        'name': stock['product_id'][1],
                        'qty_week': 0,
                        'qty_mag': stock['quantity'],
                        'qty_all': 0
                    }

            sales = products_preorder.get_sale_in_interval_date(
                date_start.strftime('%Y-%m-%d 00:00:00'),
                today.strftime('%Y-%m-%d 23:59:59'),
                count_refund=True
            )
            all_sales = products_preorder.get_sale_in_interval_date(
                '1999-01-01',
                today.strftime('%Y-%m-%d 23:59:59'),
                count_refund=True
            )

            preorders = {}
            for sale in sales:
                preorders[sale['product_id'][0]] = {
                    'object': product_model.browse(
                        sale['product_id'][0]
                    ),
                    'name': sale['product_id'][1],
                    'qty_week': sale['product_uom_qty'],
                    'qty_mag': 0,
                    'qty_all': 0
                }
            for sale in all_sales:
                if sale['product_id'][0] in preorders:
                    preorders[sale['product_id'][0]]['qty_all'] = \
                        sale['product_uom_qty']
                else:
                    preorders[sale['product_id'][0]] = {
                        'object': product_model.browse(
                            sale['product_id'][0]
                        ),
                        'name': sale['product_id'][1],
                        'qty_week': 0,
                        'qty_mag': 0,
                        'qty_all': sale['product_uom_qty']
                    }

            output = io.StringIO()
            writer = csv.writer(output)
            csvdata_preorder = ['PREORDER']
            writer.writerow(csvdata_preorder)
            csvdata = [
                'BARCODE',
                'PRODOTTO',
                'QTA SETTIMANA',
                'QTA TOTALE',
                'QTA MAGAZZINO'
            ]
            writer.writerow(csvdata)

            for prod in preorders:
                product = preorders[prod]

                line = [
                    product['object'].barcode,
                    product['name'],
                    int(product['qty_week']),
                    int(product['qty_all']),
                    int(product['qty_mag'])
                ]
                writer.writerow(line)

            writer.writerow([])

            csvdata_shipped = ['SPEDITI']
            writer.writerow(csvdata_shipped)
            writer.writerow(csvdata)

            for prod in products:
                product = products[prod]

                line = [
                    product['object'].barcode,
                    product['name'],
                    int(product['qty_week']),
                    int(product['qty_all']),
                    int(product['qty_mag'])
                ]
                writer.writerow(line)

        name = 'export_multiplayer_com_' + self.name + '_' + \
               str(date.today()) + '.csv'
        data_bytes = output.getvalue().encode("utf-8")
        attachment = {
            'name': name,
            'datas': base64.b64encode(data_bytes).decode(),
        }

        attachment_id = self.env['ir.attachment'].create(attachment)

        output.close()

        return attachment_id

    # FUNZIONI STATS #
    def get_products_in_preorder(self):
        # ritorna un queryset di prodotti
        # di questo fornitore che sono in preordine
        self.ensure_one()
        today = datetime.now()
        products = self.env['product.product'].search([
            ('seller_ids.name', '=', self.id),
            ('out_date', '>', today.strftime('%Y-%m-%d %H:%M:%S')),
            ('company_id', '=', self.env.user.company_id.id)
        ])
        return products

    def get_products_in_stock(self):
        # ritorna  prodotti che sono sicuramente in magazzino di quel fornitore
        self.ensure_one()
        wh = self.env.ref('stock.stock_location_stock').id
        domain = [
            ('location_id', '=', wh),
            ('product_id.seller_ids.name', '=', self.id),
            ('company_id', '=', self.env.user.company_id.id)
        ]
        quants = self.env['stock.quant'].read_group(
            domain=domain,
            fields=['product_id', 'quantity'],
            groupby=['product_id']
        )
        return quants

    def get_products_shipped(self, date_start, date_finish,
                             count_refund=False):
        self.ensure_one()
        customer_stock = self.env.ref('stock.stock_location_customers').id
        stock = self.env.ref('stock.stock_location_stock').id
        # TODO: se c'è più di una stock.location Difettati li prende tutti
        defective = self.env['stock.location'].search([
            ('name', 'ilike', 'Difettati')
        ]).ids
        domain = [
            ('date', '>=', date_start),
            ('date', '<=', date_finish),
            ('state', '=', 'done'),
            ('product_id.seller_ids.name', '=', self.id),
            ('company_id', '=', self.env.user.company_id.id),
            ('location_dest_id', '=', customer_stock),
            ('location_id', '=', stock)
        ]

        moves = self.env['stock.move'].read_group(
            domain=domain,
            fields=['product_id', 'product_uom_qty'],
            groupby=['product_id']
        )
        if count_refund:
            location_dest = [stock]
            location_dest.extend(defective)
            domain = [
                ('date', '>=', date_start),
                ('date', '<=', date_finish),
                ('state', '=', 'done'),
                ('company_id', '=', self.env.user.company_id.id),
                ('partner_id', '=', self.id),
                ('location_id', '=', customer_stock),
                ('location_dest_id', 'in', location_dest)
            ]
            refunds = self.env['stock.move'].read_group(
                domain=domain,
                fields=['product_id', 'product_uom_qty'],
                groupby=['product_id']
            )
            refs = {}
            for ref in refunds:
                refs[ref['product_id'][0]] = {
                    'qta': ref['product_uom_qty'],
                    'product_id_count': ref['product_id_count']
                }
            for move in moves:
                if move['product_id'][0] in refs.keys():
                    move['product_uom_qty'] = \
                        move['product_uom_qty'] - \
                        refs[move['product_id'][0]]['qta']
                    move['product_id_count'] = \
                        move['product_id_count'] - \
                        refs[move['product_id'][0]]['product_id_count']

        return moves

    def get_purchase_products(self):
        self.ensure_one()

        purchase_lines = self.env['purchase.order.line'].read_group(
            domain=[
                ('order_id.state', '=', 'purchase'),
                ('order_id.partner_id', '=', self.id)
            ], fields=['product_id', 'product_qty'], groupby=['product_id']
        )

        products = {}

        for line in purchase_lines:
            if line['product_id'][0] not in products.keys():
                products[line['product_id'][0]] = 0

            products[line['product_id'][0]] += line['product_qty']

        return products

    def button_download_report(self):
        new_attach = self.sudo().generate_monday_report()
        return {
            'type': 'ir.actions.act_window',
            'name': '%s' % new_attach[0].name,
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'res_id': new_attach[0].id,
            'target': 'current',
        }
