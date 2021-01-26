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
        result = self.search([('supplier', '=', True), ('active', '=', True), ('parent_id', '=', False)])
        supplier = []
        for res in result:
            supplier.append({'id': res.id, 'name': res.name})
        return supplier


'''

    # TODO: Porting if we need them

    def generate_monday_report(self):
        self.ensure_one()
        if self.supplier and len(self.parent_id) == 0:
            products_preorder = self.get_products_in_preorder()
            # devo recuperare i prodotti spediti che non stanno più in stock
            date_start = date.today() - timedelta(days=7)
            today = date.today()

            prods = []
            products = {}
            shipped = self.get_products_shipped(date_start.strftime('%Y-%m-%d 00:00:00'), today.strftime('%Y-%m-%d 23:59:59'), count_refund=True)
            for s in shipped:
                prods.append(s['product_id'][0])
                products[s['product_id'][0]] = {
                    'object': self.env['product.product'].browse(s['product_id'][0]),
                    'name': s['product_id'][1],
                    'qty_week': s['product_uom_qty'],
                    'qty_mag': 0,
                    'qty_all': 0
                }
            p_a = self.env['product.product'].search([('id', 'in', prods)])
            moves = p_a.get_shipped_in_interval_date('1999-01-01', today.strftime('%Y-%m-%d 23:59:59'), supplier=self.id, count_refund=True)
            for m in moves:
                if m['product_id'][0] in products:
                    products[m['product_id'][0]]['qty_all'] = m['product_uom_qty']

            products_stock = self.get_products_in_stock()
            pids_stock = []
            for p in products_stock:
                pids_stock.append(p['product_id'][0])
            ps = self.env['product.product'].search([('id', 'in', pids_stock)])
            stock_moves_all = ps.get_shipped_in_interval_date('1999-01-01', today.strftime('%Y-%m-%d 23:59:59'), supplier=self.id, count_refund=True)
            stock_moves_week = ps.get_shipped_in_interval_date(date_start.strftime('%Y-%m-%d 00:00:00'), today.strftime('%Y-%m-%d 23:59:59'), supplier=self.id, count_refund=True)
            for s in stock_moves_week:
                if s['product_id'][0] not in products:
                    products[s['product_id'][0]] = {
                        'object': self.env['product.product'].browse(s['product_id'][0]),
                        'name': s['product_id'][1],
                        'qty_week': s['product_uom_qty'],
                        'qty_mag': 0,
                        'qty_all': 0
                    }
            for s in stock_moves_all:
                if s['product_id'][0] in products:
                    products[s['product_id'][0]]['qty_all'] = s['product_uom_qty']
                else:
                    products[s['product_id'][0]] = {
                        'object': self.env['product.product'].browse(s['product_id'][0]),
                        'name': s['product_id'][1],
                        'qty_week': 0,
                        'qty_mag': 0,
                        'qty_all': s['product_uom_qty']
                    }

            for s in products_stock:
                if s['product_id'][0] in products:
                    products[s['product_id'][0]]['qty_mag'] = s['qty']
                else:
                    products[s['product_id'][0]] = {
                        'object': self.env['product.product'].browse(s['product_id'][0]),
                        'name': s['product_id'][1],
                        'qty_week': 0,
                        'qty_mag': s['qty'],
                        'qty_all': 0
                    }

            sale = products_preorder.get_sale_in_interval_date(date_start.strftime('%Y-%m-%d 00:00:00'), today.strftime('%Y-%m-%d 23:59:59'), count_refund=True)
            sale_all = products_preorder.get_sale_in_interval_date('1999-01-01', today.strftime('%Y-%m-%d 23:59:59'), count_refund=True)

            preorders = {}
            for s in sale:
                preorders[s['product_id'][0]] = {
                    'object': self.env['product.product'].browse(s['product_id'][0]),
                    'name': s['product_id'][1],
                    'qty_week': s['product_uom_qty'],
                    'qty_mag': 0,
                    'qty_all': 0
                }
            for s in sale_all:
                if s['product_id'][0] in preorders:
                    preorders[s['product_id'][0]]['qty_all'] = s['product_uom_qty']
                else:
                    preorders[s['product_id'][0]] = {
                        'object': self.env['product.product'].browse(s['product_id'][0]),
                        'name': s['product_id'][1],
                        'qty_week': 0,
                        'qty_mag': 0,
                        'qty_all': s['product_uom_qty']
                    }

            output = io.BytesIO()
            writer = csv.writer(output)
            csvdata = ['PREORDER']
            writer.writerow(csvdata)
            csvdata = ['BARCODE', 'PRODOTTO', 'QTA SETTIMANA', 'QTA TOTALE', 'QTA MAGAZZINO']
            writer.writerow(csvdata)

            for prod in preorders:
                product = preorders[prod]

                line = [product['object'].barcode, product['name'].encode('utf8'), int(product['qty_week']), int(product['qty_all']), int(product['qty_mag'])]
                writer.writerow(line)

            writer.writerow([])

            csvdata = ['SPEDITI']
            writer.writerow(csvdata)
            csvdata = ['BARCODE', 'PRODOTTO', 'QTA SETTIMANA', 'QTA TOTALE', 'QTA MAGAZZINO']
            writer.writerow(csvdata)

            for prod in products:
                product = products[prod]

                line = [product['object'].barcode, product['name'].encode('utf8'), int(product['qty_week']), int(product['qty_all']), int(product['qty_mag'])]
                writer.writerow(line)

        name = 'export_multiplayer_com_' + self.name + '_' + str(date.today()) + '.csv'

        attachment = {
            'name': name,
            'datas_fname': name,
            'datas': base64.b64encode(output.getvalue()).decode(),
        }

        attachment_id = self.env['ir.attachment'].create(attachment)

        output.close()

        return attachment_id

    # FUNZIONI STATS #
    def get_products_in_preorder(self):
        # ritorna un queryset di prodotti di questo fornitore che sono in preordine
        self.ensure_one()
        today = datetime.now()
        products = self.env['product.product'].search([('seller_ids.name', '=', self.id), ('out_date', '>', today.strftime('%Y-%m-%d %H:%M:%S')), ('company_id', '=', self.env.user.company_id.id)])
        return products

    def get_products_in_stock(self):
        # ritorna  prodotti che sono sicuramente in magazzino di quel fornitore
        self.ensure_one()
        # TODO: Trovare un metodo equivalente per cercae le stesse informazioni
        # wh = self.env.ref('stock.stock_location_stock').id
        # domain = [('location_id', '=', wh), ('partner_id', '=', self.id), ('company_id', '=', self.env.user.company_id.id)]
        # quants = self.env['stock.quant'].read_group(domain=domain, fields=['product_id', 'qty', 'inventory_value'], groupby=['product_id'])
        # return quants
        return self.env['stock.quant']

    def get_products_shipped(self, date_start, date_finish, count_refund=False):
        self.ensure_one()
        customer_stock = self.env.ref('stock.stock_location_customers').id
        stock = self.env.ref('stock.stock_location_stock').id
        difettati = self.env['stock.location'].search([('name', 'ilike', 'Difettati')]).id
        domain = [('date', '>=', date_start), ('date', '<=', date_finish), ('state', '=', 'done'), ('partner_id', '=', self.id),
            ('company_id', '=', self.env.user.company_id.id), ('location_dest_id', '=', customer_stock), ('location_id', '=', stock)]

        moves = self.env['stock.move'].read_group(domain=domain, fields=['product_id', 'product_uom_qty'], groupby=['product_id'])
        if count_refund:
            domain = [('date', '>=', date_start), ('date', '<=', date_finish), ('state', '=', 'done'),
            ('company_id', '=', self.env.user.company_id.id), ('partner_id', '=', self.id), ('location_id', '=', customer_stock), ('location_dest_id', 'in', [stock, difettati])]
            refunds = self.env['stock.move'].read_group(domain=domain, fields=['product_id', 'product_uom_qty'], groupby=['product_id'])
            refs = {}
            for ref in refunds:
                refs[ref['product_id'][0]] = {
                    'qta': ref['product_uom_qty'],
                    'product_id_count': ref['product_id_count']
                }
            for move in moves:
                if move['product_id'][0] in refs.keys():
                    move['product_uom_qty'] = move['product_uom_qty'] - refs[move['product_id'][0]]['qta']
                    move['product_id_count'] = move['product_id_count'] - refs[move['product_id'][0]]['product_id_count']

        return moves

    #################

    def get_purchase_products(self):
        self.ensure_one()

        purchase_lines = self.env['purchase.order.line'].read_group(domain = [('order_id.state','=','purchase'),('order_id.partner_id','=',self.id)], fields = ['product_id','product_qty'], groupby = ['product_id'])

        products = {}

        for line in purchase_lines:
            if line['product_id'][0] not in products.keys():
                products[line['product_id'][0]] = 0

            products[line['product_id'][0]] += line['product_qty']

        return products

    def download_report(self):
        new_attach = self.sudo().generate_monday_report()
        return {
            'type': 'ir.actions.act_window',
            'name': '%s' % new_attach[0].name,
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'res_id': new_attach[0].id,
            'target': 'current',
        }
    '''
