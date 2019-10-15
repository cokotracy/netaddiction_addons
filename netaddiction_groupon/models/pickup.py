# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import Warning
from collections import defaultdict
import datetime
from ftplib import FTP
import io
import csv
import base64

class GrouponPickup(models.Model):
    _name = 'groupon.pickup.wave'

    name = fields.Char(string="Nome")
    order_ids = fields.One2many(comodel_name='netaddiction.groupon.sale.order', string='Ordini', inverse_name="wave_id")
    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('done', 'Completato'),
    ], string='Stato', readonly=True, default="draft")
    date_close = fields.Datetime(string="Data Chiusura")
    tracking_file = fields.Binary(string="Tracking file")

    @api.model
    def get_picks(self, wave_id):
        wave = self.browse(int(wave_id))
        picks = []
        for order in wave.order_ids:
            for pick in order.picking_ids:
                picks.append({'id': pick.id, 'barcode': pick.delivery_barcode, 'name': pick.partner_id.name, 'groupon_id': order.groupon_number, 'pick_barcode': pick.barcode_image})
        return picks

    @api.one
    def close(self):
        self.state = 'done'
        for order in self.order_ids:
            order.close()
            for pick in order.picking_ids:
                now = datetime.date.today()
                manifest = self.env['netaddiction.manifest'].search([('date', '=', now), ('carrier_id', '=', pick.carrier_id.id)])
                if len(manifest) == 0:
                    man_id = self.env['netaddiction.manifest'].create({'date': now, 'carrier_id': pick.carrier_id.id}).id
                else:
                    man_id = manifest.id

                pick.write({'manifest': man_id, 'delivery_read_manifest': False})

    @api.one
    def unlink(self):
        if self.state == 'draft':
            return super(GrouponPickup, self).unlink()

        raise Warning("Non puoi cancellare una lista prelievo completata.")

    @api.model
    def create_wave(self):
        orders = self.env['netaddiction.groupon.sale.order'].search([('state', '=', 'draft'), ('picking_ids', '!=', False), ('wave_id', '=', False)])

        if len(orders) > 0:
            ids = []
            problem_order = []
            for order in orders:
                if len(order.partner_shipping_id.street) > 30:
                    order.state = 'problem'
                    problem_order.append(order.name)
                else:
                    ids.append(order.id)
            if len(ids) > 0:
                attr = {
                    'order_ids': [(6, False, ids)],
                }
                wave = self.create(attr)
                wave.name = 'Lista Groupon %s' % (wave.id)
                if len(problem_order) > 0:
                    return 'Lista creata ma ci sono ordini con indirizzo troppo lungo: %s' % (problem_order)
                else:
                    return 'ok'
            else:
                if len(problem_order) > 0:
                    return 'Ci sono ordini con indirizzo troppo lungo: %s' % (problem_order)
                else:
                    return 'Non ci sono ordini da pickuppare.'
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

    @api.model
    def pickup_product(self, wave, product_id, shelf, qty):
        wave = int(wave)
        product_id = int(product_id)
        shelf = int(shelf)
        qty = int(qty)
        results = self.env['netaddiction.groupon.sale.order'].search([('product_id.id', '=', product_id), ('wave_id.id', '=', wave)])

        if len(results) == 0:
            return {'result': 0, 'error': 'Prodotto non presente in lista'}

        allocations = self.env['groupon.wh.locations.line'].search([('product_id.id', '=', product_id), ('wh_location_id.id', '=', shelf)])

        if len(allocations) == 0:
            return {'result': 0, 'error': 'Il prodotto non risulta allocato'}

        if allocations.qty < qty:
            return {'result': 0, 'error': 'Il prodotto risulta allocato con quantità inferiore a quella da scalare'}

        allocations.decrease(qty)

        for res in results:
            for picks in res.picking_ids:
                for pick in picks.pack_operation_product_ids:
                    if pick.product_id.id == product_id:
                        remaining = pick.product_qty - pick.qty_done
                        if remaining <= qty:
                            pick.qty_done = pick.product_qty
                            qty -= pick.product_qty
                        else:
                            pick.qty_done = pick.qty_done + qty
                            qty = 0

        return {'ok': 'ok'}

    @api.multi
    def get_ldv(self):
        ftp = FTP('ftp.sda.it')
        ftp.login('cli_c54566', 'inet54566')
        ftp.cwd('send')
        report_name = 'Report.Log'
        report = open(report_name, 'wb')
        ftp.retrbinary('RETR %s' % report_name, report.write)
        report.close()

        rfile = open(report_name, "r")
        ldv = {}
        for line in rfile.readlines():
            sp = line.split('-')
            name = sp[3].strip()
            if name[0:3] == 'LDV':
                ldv[sp[0].strip()] = name
        dates = {}
        for r in ldv:
            dt = datetime.datetime.strptime(r, '%Y/%m/%d %H:%M:%S')
            dates[dt] = ldv[r]
        last = sorted(dates)[-1]
        to_download = dates[last]
        rfile.close()

        csv_file = open(to_download, "wb")
        ftp.retrbinary('RETR %s' % to_download, csv_file.write)
        csv_file.close()
        self.process_ldv(to_download)
        ftp.close()

    @api.one
    def process_ldv(self, file):
        ifile = open(file, "rb")
        reader = csv.reader(ifile)
        for row in reader:
            if len(row) > 2:
                barcode = row[4].strip()
                pick = self.env['stock.picking'].search([('delivery_barcode', '=', barcode)])
                if pick:
                    pick.carrier_tracking_ref = row[0].strip()

    @api.one
    def generate_tracking(self):
        output = io.BytesIO()
        writer = csv.writer(output)
        csvdata = ['fulfillment_line_item_id', 'carrier' 'tracking_1', 'tracking_2', 'tracking_3', 'tracking_4', 'tracking_5', 'tracking_6', 'inventory_decrement_date']
        writer.writerow(csvdata)

        for order in self.order_ids:
            pick = order.picking_ids[0]
            csvdata = [order.groupon_number, 'SDA Express', pick.carrier_tracking_ref, '', '', '', '', '', datetime.datetime.now().strftime('%d/%m/%Y')]
            writer.writerow(csvdata)
        self.tracking_file = base64.b64encode(output.getvalue()).decode()
        output.close()
