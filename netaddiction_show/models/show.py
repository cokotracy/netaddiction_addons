# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
import datetime
import io
import csv
import base64
from odoo.exceptions import Warning


class Show(models.Model):
    _name = "netaddiction.show"
    _description = "Netaddiction Show"

    name = fields.Char(
        string="Nome Fiera"
    )

    show_quant_ids = fields.One2many(
        comodel_name='netaddiction.show.quant',
        inverse_name='name',
        string='Prodotti Partiti'
    )

    show_return_ids = fields.One2many(
        comodel_name='netaddiction.return.quants',
        inverse_name='name',
        string='Prodotti Rientrati'
    )

    show_sell_ids = fields.One2many(
        comodel_name='netaddiction.sell.quant',
        inverse_name='name',
        string='Prodotti Venduti'
    )

    show_difference_ids = fields.One2many(
        comodel_name='netaddiction.difference.quant',
        inverse_name='name',
        string='Differenze'
    )

    date_start = fields.Date(
        string="Data inizio"
    )

    date_finish = fields.Date(
        string="Data fine"
    )

    state = fields.Selection(
        string="Stato",
        selection=[
            ('draft', 'Nuova'),
            ('open', 'Aperta'),
            ('close', 'Chiusa')],
        default="draft")

    exit_value = fields.Float(string="Valore acquistato uscito",
        help='Valore totale dei prodotti partiti per la fiera calcolato '
        'con i prezzi di carico secondo FIFO nel momento di creazione',
        # compute="_get_exit_value"
    )

    exit_sell_value = fields.Float(string="Valore ipotetico venduto uscito",
        help='Valore ipotetico di vendita dei prodotti partiti per la fiera '
        'calcolato con i prezzi al pubblico nel momento di creazione',
        # compute="_get_sell_value"
    )

    export_file = fields.Binary(
        string="Csv",
        attachment=True
    )

    import_file = fields.Binary(
        string="Csv Ritorno Fiera",
        attachment=True
    )

    report_file = fields.Binary(
        string="Csv Ritorno Fiera",
        attachment=True
    )

    sale_stock_value = fields.Float(
        string="Valore acquistato venduto",
        # compute="_get_sale_stock_value"
    )

    sale_sell_value = fields.Float(
        string="Valore venduto",
        # compute="_get_sale_sell_value"
    )

    @api.multi
    def close_show(self):
        for record in self:
            record.state = 'close'

    '''
    @api.one
    def _get_sale_stock_value(self):
        value = 0
        for line in self.show_sell_ids:
            value += float(line.stock_value)
        self.sale_stock_value = value

    @api.one
    def _get_sale_sell_value(self):
        value = 0
        for line in self.show_sell_ids:
            value += float(line.public_price)
        self.sale_sell_value = value
    '''

    @api.multi
    def import_csv(self):
        csv_file = base64.b64decode(self.import_file).decode('utf-8')
        csv_bytes = io.StringIO(csv_file)
        spamreader = csv.reader(csv_bytes)
        product_model = self.env['product.product']
        show_quant_model = self.env['netaddiction.show.quant']
        sell_quant_model = self.env['netaddiction.sell.quant']

        for line in spamreader:
            barcode = line[0]
            if barcode == 'Barcode':
                continue

            barcodes = [
                barcode,
                barcode[1:],
                '0' + barcode,
                barcode.lower(),
                barcode.upper(),
                barcode.capitalize()]

            product = product_model.search(
                [('barcode', 'in', barcodes)])
            if product:
                value = 0
                res = show_quant_model.search(
                    [('product_id', '=', product.id), ('name', '=', self.id)])
                if res:
                    q = 0
                    tot = 0
                    for pid in res:
                        tot += pid.stock_value
                        q += pid.qty
                    value = float(tot) / float(q)

                attr = {
                    'name': self.id,
                    'product_id': product.id,
                    'date_move': datetime.date.today(),
                    'qty': line[3],
                    'public_price': line[4],
                    'stock_value': value * float(line[3])
                }
                sell_quant_model.create(attr)

    @api.multi
    def create_csv(self):
        self.ensure_one()
        tax_inc = self.env.ref('l10n_it.1_22v INC').id
        products = {}
        for pid in self.show_quant_ids:
            if pid.product_id.id in products:
                products[pid.product_id.id]['qty'] += pid.qty
            else:
                tr = 'R2'
                for tax in pid.product_id.taxes_id:
                    if tax.id == tax_inc:
                        tr = 'R1'
                products[pid.product_id.id] = {
                    'name': pid.product_id.display_name,
                    'qty': pid.qty,
                    'price': pid.public_price,
                    'unit_value': pid.stock_value / float(pid.qty),
                    'barcode': pid.product_id.barcode,
                    'iva': tr
                }

        output = io.StringIO()
        writer = csv.writer(output)

        for pid in products:
            product = products[pid]
            csvdata = [
                product['name'].encode("utf8"),
                product['barcode'],
                product['price'],
                product['qty'],
                product['unit_value'],
                'Multiplayer.com',
                product['iva']]
            writer.writerow(csvdata)

        self.export_file = output.getvalue()
        output.close()

    '''
    @api.one
    def _get_exit_value(self):
        value = 0
        for line in self.show_quant_ids:
            value += float(line.stock_value)
        self.exit_value = value

    @api.one
    def _get_sell_value(self):
        value = 0
        for line in self.show_quant_ids:
            value += float(line.qty) * float(line.public_price)
        self.exit_sell_value = value

    @api.model
    def add_quant_to_show(self, location_id, qta, show_id):
        show_id = int(show_id)
        this_show = self.browse(show_id)

        location = self.env['netaddiction.wh.locations.line'].browse(
            int(location_id))
        stock_show = self.env.ref(
            'netaddiction_show.netaddiction_stock_show').id
        picking_type_show = self.env.ref(
            'netaddiction_show.netaddiction_type_out_show').id
        wh_stock = self.env.ref('stock.stock_location_stock').id

        if int(qta) <= 0:
            return 'Dai, serio, mi stai prendendo per i fondelli. ' \
                'Come pretendi di spostare una quantità negativa?'
        if int(qta) > int(location.product_id.qty_available_now):
            return 'Non puoi scaricare più prodotti di quelli disponibili'
        if int(qta) > int(location.qty):
            return'Non puoi scaricare più prodotti di quelli '\
                'che contiene lo scaffale'

        # per prima cosa decremento la quantità sulla locazione
        diff = location.qty - int(qta)
        location.qty = diff
        # location.decrease(int(qta))
        # faccio gli spostamenti dal magazzino stock a quello fiere
        attr = {
            'picking_type_id': picking_type_show,
            'move_type': 'one',
            'priority': '1',
            'location_id': wh_stock,
            'location_dest_id': stock_show,
            'move_lines': [(0, 0, {'product_id': location.product_id.id,
                                   'product_uom_qty': int(qta),
                'state': 'draft',
                'product_uom': location.product_id.uom_id.id,
                'name': 'WH/Stock > Magazzino Fiera',
                'origin': this_show.name})],
        }
        pick = self.env['stock.picking'].sudo().create(attr)
        pick.sudo().action_confirm()
        pick.sudo().force_assign()
        for line in pick.pack_operation_product_ids:
            line.sudo().write({'qty_done': line.product_qty})
        pick.sudo().do_transfer()

        quant_list = []
        inventory_value = 0
        for move in pick.sudo().move_lines:
            for q in move.quant_ids:
                quant_list.append(q.id)
                inventory_value += q.inventory_value

        data = {
            'name': show_id,
            'product_id': location.product_id.id,
            'date_move': datetime.date.today(),
            'qty': qta,
            'public_price': location.product_id.lst_price,
            'pick_id': pick.id,
            'quant_ids': [(6, False, quant_list)],
            'stock_value': inventory_value
        }
        self.env['netaddiction.show.quant'].sudo().create(data)

        if diff == 0:
            location.sudo().unlink()

        return 1

    @api.one
    def difference(self):
        gone = {}
        sell = {}
        returned = {}
        for line in self.show_quant_ids:
            if line.product_id in gone.keys():
                gone[line.product_id]['qta'] += line.qty
                gone[line.product_id]['value'] += (line.stock_value / line.qty)
            else:
                gone[line.product_id] = {
                    'qta': line.qty,
                    'value': (line.stock_value / line.qty)
                }
        for line in self.show_sell_ids:
            if line.product_id in sell.keys():
                sell[line.product_id]['qta'] += line.qty
                sell[line.product_id]['value'] += line.public_price
                sell[line.product_id]['stock_value'] += line.stock_value
            else:
                sell[line.product_id] = {
                    'qta': line.qty,
                    'value': line.public_price,
                    'stock_value': line.stock_value
                }
        for line in self.show_return_ids:
            if line.product_id in returned.keys():
                returned[line.product_id]['qta'] += line.qty
            else:
                returned[line.product_id] = {
                    'qta': line.qty
                }

        difference = {}
        report = {}
        for product in gone:
            sell_qty = 0
            sell_value = 0
            sell_stock = 0
            if product in sell.keys():
                sell_qty = sell[product]['qta']
                sell_value = sell[product]['value']
                sell_stock = sell[product]['stock_value']
            returned_qty = 0
            if product in returned.keys():
                returned_qty = returned[product]['qta']

            report[product] = {
                'gone': gone[product]['qta'],
                'value_gone': gone[product]['value'],
                'sell': sell_qty,
                'value_sell': sell_value,
                'value_sell_stock': sell_stock,
                'returned': returned_qty
            }

            diff = gone[product]['qta'] - sell_qty
            if diff != returned_qty:
                difference[product] = {
                    'gone': gone[product]['qta'],
                    'sell': sell_qty,
                    'returned': returned_qty,
                    'diff': (diff - returned_qty)
                }

        for d in difference:
            attr = {
                'name': self.id,
                'product_id': d.id,
                'gone': difference[d]['gone'],
                'sell': difference[d]['sell'],
                'returned': difference[d]['returned'],
                'diff': difference[d]['diff'],
                'date_move': datetime.date.today(),
            }
            self.env['netaddiction.difference.quant'].create(attr)

        output = io.BytesIO()
        writer = csv.writer(output)
        csvdata = [
            'Nome',
            'Partita',
            'Valore Partita',
            'Venduta',
            'Fatturato Venduta',
            'Valore Venduta',
            'Ritornata']
        writer.writerow(csvdata)
        for product in report:
            csvdata = [
                product.display_name.encode('utf8'),
                report[product]['gone'],
                report[product]['value_gone'],
                report[product]['sell'],
                report[product]['value_sell'],
                report[product]['value_sell_stock'],
                report[product]['returned']]
            writer.writerow(csvdata)
        self.report_file = base64.b64encode(output.getvalue()).decode()
        output.close()

    @api.model
    def verify_old_pickup(self, barcodes):
        result = {
            'qta': 0
        }
        product = self.env['product.product'].search(
            [('barcode', 'in', barcodes)])
        if product:
            quants = self.env['netaddiction.show.quant'].search(
                [('product_id', '=', product.id)])
            qta = 0
            for q in quants:
                qta += q.qty
            result['qta'] = qta

        return result
    '''


class DiffQuant(models.Model):
    _name = "netaddiction.difference.quant"
    _description = "Netaddiction Difference Quant"

    name = fields.Many2one(
        comodel_name="netaddiction.show",
        string="Fiera"
    )
    
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Prodotto"
    )
    
    date_move = fields.Date(
        string="Data Creazione"
    )

    diff = fields.Integer(
        string="Differenza"
    )

    gone = fields.Integer(
        string="Partita"
    )

    sell = fields.Integer(
        string="Venduta"
    )

    returned = fields.Integer(
        string="Ritornata"
    )


class ShowQuant(models.Model):
    _name = "netaddiction.show.quant"
    _description = "Netaddiction Show Quant"

    name = fields.Many2one(
        comodel_name="netaddiction.show",
        string="Fiera"
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Prodotto"
    )

    date_move = fields.Date(
        string="Data spostamento"
    )

    qty = fields.Integer(
        string="Quantità"
    )

    stock_value = fields.Float(
        string="Valore acquistato"
    )

    public_price = fields.Float(
        string="Prezzo al pubblico"
    )

    quant_ids = fields.Many2many(
        string="Rigo Magazzino",
        comodel_name="stock.quant"
    )

    pick_id = fields.Many2one(
        string="Picking",
        comodel_name="stock.picking"
    )


class SellQuant(models.Model):
    _name = "netaddiction.sell.quant"
    _description = "Netaddiction Sell Quant"

    name = fields.Many2one(
        comodel_name="netaddiction.show",
        string="Fiera")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Prodotto")

    date_move = fields.Date(
        string="Data Creazione"
    )

    qty = fields.Integer(
        string="Quantità"
    )

    public_price = fields.Float(
        string="Prezzo al pubblico Totale"
    )

    stock_value = fields.Float(
        string="Valore acquistato"
    )


class ReturnQuant(models.Model):
    _name = "netaddiction.return.quants"
    _description = "Netaddiction Return Quants"

    name = fields.Many2one(
        comodel_name="netaddiction.show",
        string="Fiera"
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Prodotto"
    )

    date_move = fields.Date(
        string="Data Rientro"
    )

    qty = fields.Integer(
        string="Quantità"
    )


class ProductsMovement(models.TransientModel):
    _name = "netaddiction.show.returned.move"
    _description = "Netaddiction Show Returned Move"

    barcode = fields.Char(
        string="Barcode"
    )

    product_id = fields.Many2one(
        string="Prodotto",
        comodel_name="product.product"
    )

    qty_available = fields.Integer(
        string="Qtà in fiera"
    )

    show_id = fields.Many2one(
        string="Fiera",
        comodel_name="netaddiction.show"
    )

    qty_to_move = fields.Integer(
        string="Quantità da riallocare"
    )

    barcode_allocation = fields.Char(
        string="Barcode Scaffale"
    )

    # new_allocation = fields.Many2one(
    #     string="Dove Allocare",
    #     comodel_name="netaddiction.wh.locations"
    # )

    message = fields.Char(
        string="Messaggio"
    )

    '''
    @api.onchange('barcode_allocation')
    def change_alloc(self):
        loc = self.env['netaddiction.wh.locations'].search([
            ('barcode', '=', self.barcode_allocation),
            ('company_id', '=', self.env.user.company_id.id)])
        if loc:
            self.new_allocation = loc.id

    @api.onchange('barcode')
    def search_product(self):
        loc = self.env['netaddiction.wh.locations'].search([
            ('barcode', '=', '0000000001'),
            ('company_id', '=', self.env.user.company_id.id)])
        if self.barcode:
            barcodes = [
                str(self.barcode),
                '0' + str(self.barcode),
                str(self.barcode).upper(),
                str(self.barcode).lower(),
                str(self.barcode).capitalize(),
                str(self.barcode)[1:]]
            product = self.env['product.product'].sudo().search(
                [('barcode', 'in', barcodes)])
            if product:
                self.product_id = product[0].id

                if self.show_id:
                    result = self.env['netaddiction.show.quant'].search([
                        ('name', '=', self.show_id.id),
                        ('product_id', '=', product[0].id)])
                    if result:
                        qta = 0
                        for res in result:
                            qta += res.qty
                        sell = self.env['netaddiction.sell.quant'].search([
                            ('name', '=', self.show_id.id),
                            ('product_id', '=', product[0].id)])
                        if sell:
                            for s in sell:
                                qta -= s.qty
                        returned = self.env[
                            'netaddiction.return.quants'].search([
                                ('name', '=', self.show_id.id),
                                ('product_id', '=', product[0].id)])
                        if returned:
                            for s in returned:
                                qta -= s.qty
                        if qta < 0:
                            qta = 0
                        self.qty_available = qta
                        self.qty_to_move = 1
                        self.new_allocation = loc.id

                    al = ''
                    for line in product.product_wh_location_line_ids:
                        al += '%s - %s \n' % (line.qty,
                                              line.wh_location_id.name)
                    self.message = al

    @api.one
    def execute(self):
        if self.qty_to_move <= 0:
            raise Warning('Seriamente vuoi spostare una quantità '
                          'negativa o uguale a zero?')
        if self.qty_to_move > self. qty_available:
            raise Warning(
                'Ma come ti viene in mente di caricare una quantità '
                'maggiore di quella disponibile in Magazzino Fiere?!')
        if not self.show_id:
            raise Warning('Devi inserire una Fiera')
        product = self.env['netaddiction.show.quant'].search([
            ('name', '=', self.show_id.id),
            ('product_id', '=', self.product_id.id)])
        if len(product) == 0:
            raise Warning('Il prodotto che stai cercando di caricare '
                          'non fa parte della fiera selezionata')
        if not self.new_allocation:
            raise Warning('Devi selezionare un ripiano dove allocare')

        stock_show = self.env.ref(
            'netaddiction_show.netaddiction_stock_show').id
        picking_type_show = self.env.ref(
            'netaddiction_show.netaddiction_type_in_show').id
        wh_stock = self.env.ref('stock.stock_location_stock').id
        attr = {
            'picking_type_id': picking_type_show,
            'move_type': 'one',
            'priority': '1',
            'location_id': stock_show,
            'location_dest_id': wh_stock,
            'move_lines': [(0, 0, {'product_id': self.product_id.id,
                                   'product_uom_qty': int(self.qty_to_move),
                'state': 'draft',
                'product_uom': self.product_id.uom_id.id,
                'name': 'Magazzino Fiera > WH/Stock',
                'origin': self.show_id.name})],
        }
        pick = self.env['stock.picking'].sudo().create(attr)
        pick.sudo().action_confirm()
        pick.sudo().force_assign()
        for line in pick.pack_operation_product_ids:
            line.sudo().write({'qty_done': line.product_qty})
        pick.sudo().do_transfer()

        self.env['netaddiction.wh.locations.line'].sudo().allocate(
            self.product_id.id, self.qty_to_move, self.new_allocation.id)

        not_sell = {
            'name': self.show_id.id,
            'product_id': self.product_id.id,
            'qty': self.qty_to_move,
            'date_move': datetime.date.today()
        }
        self.env['netaddiction.return.quants'].sudo().create(not_sell)

        self.barcode = False
        self.product_id = False
        self.qty_available = False
        self.qty_to_move = False
        self.barcode_allocation = False
        self.message = 'Prodotto Riallocato Correttamente'
    '''
