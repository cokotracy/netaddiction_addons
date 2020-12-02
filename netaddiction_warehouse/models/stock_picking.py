import base64
import json
import pytz

from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..tools.lib_holidays import is_holiday


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    barcode_image = fields.Text(
        compute='_compute_barcode_image',
        string="Barcode image",
    )

    batch_id = fields.Many2one(
        oldname='wave_id'
    )

    date_of_shipping_home = fields.Date(
        compute='_compute_date_of_shipping',
        string="Data di consegna",
    )

    delivery_barcode = fields.Char(
        string="Barcode Spedizione"
    )

    delivery_read_manifest = fields.Boolean(
        string="Letto nel manifest",
    )

    is_b2b = fields.Boolean(
        compute='compute_b2b',
        search="search_b2b",
        string="B2B",
    )

    manifest = fields.Many2one(
        'netaddiction.manifest',
        string="Manifest",
    )

    number_of_pieces = fields.Integer(
        compute='_get_number_of_pieces',
        string="Pezzi",
    )

    # FIXME: res.partner's 'rating' field has not been migrated
    # partner_rating = fields.Selection(
    #     related='partner_id.rating',
    #     store=False
    # )

    sale_order_status = fields.Selection(
        [('draft', 'Nuovo'),
         ('sent', 'Preventivo Inviato'),
         ('sale', 'In Lavorazione'),
         ('partial_done', 'Parzialmente Completato'),
         ('problem', 'Problema'),
         ('done', 'Completato'),
         ('cancel', 'Annullato')],
        compute='_get_sale_order_status',
        readonly=True,
        string="Stato Ordine",
    )

    sale_order_payment_method = fields.Many2one(
        'account.journal',
        compute='_get_sale_order_payment',
        string="Metodo di pagamento",
    )

    total_import = fields.Float(
        compute='_get_total_import',
        string="Importo",
    )

    def _get_sale_order_status(self):
        for pick in self:
            pick.sale_order_status = pick.sale_id.state

    def _get_sale_order_payment(self):
        for pick in self:
            pick.sale_order_payment_method = pick.sale_id.payment_method_id

    def _compute_date_of_shipping(self):
        for pick in self:
            if pick.scheduled_date:
                date_ship = pick.scheduled_date
            else:
                date_ship = datetime.now()
            date_ship += timedelta(days=pick.carrier_id.time_to_shipping)
            while is_holiday(date_ship):
                date_ship += timedelta(days=1)
            pick.date_of_shipping_home = date_ship

    def _add_delivery_cost_to_so(self):
        pass

    ##################################
    # FUNCTION PER CONTROLLO PICK UP #
    ##################################

    @api.model
    def do_validate_orders(self, pick_id):
        pick = self.search([('id', '=', int(pick_id))])

        if pick.sale_id.state in ['problem', 'cancel']:
            text = "La spedizione %s dell'ordine %s non può essere spedita" \
                   " perchè lo stato non è in lavorazione, l'ordine verrà" \
                   " tolto dalla lista. Ricordati di ricaricare i prodotti"\
                   % (pick.name, pick.sale_id.name)
            if pick.sale_id.state == 'problem':
                pick.write({
                    'batch_id': False,
                    'move_line_ids': [
                        (1, i, {'qty_done': 0})
                        for i in pick.move_line_ids.ids
                    ]
                })
            return {'error': text, 'id': pick.id}

        # for pay in this.sale_id.account_payment_ids:
        #    if this.total_import == pay.amount and pay.state == 'posted'

        if pick._check_backorder():
            wiz = self.env['stock.backorder.confirmation'].create(
                {'pick_ids': pick.ids}
            )
            wiz.process()
            backorder_pick = self.env['stock.picking'].search(
                [('backorder_id', '=', pick.id)]
            )
            backorder_pick.write({'batch_id': False})

        pick.button_validate()

        partial = any(p.state != 'done' for p in pick.sale_id.picking_ids)
        pick.sale_id.state = 'partial_done' if partial else 'done'

        # a questo punto metto spedita e da fatturare anche la riga spedizioni
        shipping_line = self.env['sale.order.line'].search(
            [('order_id', '=', pick.sale_id.id),
             ('price_unit', '=', round(pick.carrier_price, 2)),
             ('qty_delivered', '=', 0),
             '|',
             ('is_delivery', '=', True),
             ('is_payment', '=', True)],
            limit=1
        )
        if shipping_line:
            shipping_line.write({
                'qty_delivered': 1,
                'qty_to_invoice': 1
            })

        if not self.search_count(
            [('batch_id', '=', pick.batch_id.id),
             ('state', 'not in', ['draft', 'cancel', 'done'])]
        ):
            pick.batch_id.done()

        now = datetime.now(tz=pytz.timezone(self.env.user.tz or 'UTC'))
        # cerco la presenza di un manifest
        manifest = self.env['netaddiction.manifest'].search(
            [('date', '=', now.date()),
             ('carrier_id', '=', pick.carrier_id.id)]
        )
        if not manifest:
            # manifest per questo corriere non presente
            man_id = self.env['netaddiction.manifest'].create(
                {'date': now, 'carrier_id': pick.carrier_id.id}
            ).id
        else:
            man_id = manifest.id

        pick.write({'manifest': man_id, 'delivery_read_manifest': False})
        # fattura
        # new_invoices = this.sale_id.action_invoice_create()
        # sequenza fattura
        # sequence = self.env['ir.sequence'].search([('company_id','=',1),('name','ilike','Clienti')])
        # prefix = sequence.prefix
        # now = datetime.datetime.now()
        # next_number = 1
        # number = prefix.replace('%(range_year)s',str(datetime.date.today().year))

        # for line in sequence.date_range_ids:
        #    if datetime.datetime.strptime(line.date_from,'%Y-%m-%d') <= now and datetime.datetime.strptime(line.date_to,'%Y-%m-%d') >= now:
        #        next_number = line.number_next
        #        number = prefix.replace('%(range_year)s',str(datetime.date.today().year))
        #        line.write({
        #                'number_next':int(line.number_next) + int(sequence.number_increment),
        #                'number_next_actual':int(line.number_next_actual) + int(sequence.number_increment)
        #            })
        #
        # prefix = sequence.prefix
        # fill = str(next_number).zfill(sequence.padding)

        # for i in new_invoices:
        #    this_inv = self.env['account.invoice'].search([('id','=',i)])
        #    this_inv.invoice_validate()
        #    this_inv.write({
        #        'number' : number + fill,
        #        'name' : number + fill,
        #        })

    @api.model
    def confirm_reading_manifest(self, pick):
        picking = self.search([('id', '=', int(pick))])

        # controllo che lo stato dell'ordine sia ancora completato
        if picking.state != 'done':
            picking.manifest = False
            return {'state': 'problem',
                    'message': 'L\'ordine è stato annullato'}

        picking.delivery_read_manifest = True
        return {'state': 'ok'}

    def generate_barcode(self):
        """
        genera il barcode della spedizione
        """
        self.ensure_one()

        brt = self.env.ref('netaddiction_warehouse.carrier_brt')

        if self.carrier_id == brt:
            self.delivery_barcode = self._generate_barcode_bartolini()
        else:
            self.delivery_barcode = self._generate_barcode_sda()

        self.carrier_tracking_ref = self.delivery_barcode

    def _generate_barcode_bartolini(self):
        """
        creo un barcode univoco "nel mese"
        con prefix + idordine
        """
        self.ensure_one()
        return ''.join(['CC0271', str(self.id).zfill(9)])

    def _generate_barcode_sda(self):
        self.ensure_one()
        return str(self.id).zfill(13)

    @api.model
    def do_multi_validate_orders(self, picks):
        ids = {'error': [], 'print': []}
        for p in picks:
            res = self.do_validate_orders(p)
            if res:
                ids['error'].append(res['id'])
            else:
                ids['print'].append(p)

        if len(ids['error']) > 0:
            return ids

    def verify_quantity(self):
        # verifica che la quantità dei prodotti di questa spedizione sia
        # uguale o maggiore a quella dell'ordine
        self.ensure_one()
        out_pick_type = self.env.ref('stock.picking_type_out')

        qty_sale = 0
        for line in self.sale_id.order_line:
            if not line.is_delivery and not line.is_payment:
                qty_sale += line.product_uom_qty

        qty_pick = 0
        for pick in self.sale_id.picking_ids:
            if pick.picking_type_id == out_pick_type:
                for line in pick.move_lines:
                    qty_pick += line.product_qty

        return qty_pick >= qty_sale

    def compute_b2b(self):
        for pick in self:
            pick.is_b2b = pick.sale_id.is_b2b

    def search_b2b(self, operator, value):
        if operator not in ('=', '!='):
            raise ValueError('Dominio invalido per ricerca B2B')
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('sale_id.is_b2b', '=', True)]
        return [('sale_id.is_b2b', '=', False)]

    def _compute_barcode_image(self):
        for pick in self:
            barcode = self.env['ir.actions.report'].barcode(
                'Code128',
                pick.delivery_barcode,
                width=448,
                height=50,
                humanreadable=0
            )
            barcode_base64 = base64.b64encode(barcode)
            pick.barcode_image = 'data:image/png;base64,' + barcode_base64

    def action_cancel(self):
        cancel = []
        for pick in self:
            if pick.delivery_read_manifest:
                raise ValidationError(
                    "Non puoi annullare la spedizione in quanto è già in"
                    " carico al corriere"
                )
            if pick.payment_id.state != 'posted':
                # cancello tutto
                cancel.append(pick.payment_id)
                continue

            products = []
            for move in pick.move_lines:
                products.append(move.product_id.id)
            for move_line in pick.move_line_ids:
                products.append(move_line.product_id.id)

            for inv in pick.payment_id.invoice_ids:
                ref = inv._reverse_moves()
                for line in ref.line_ids:
                    if line.product_id.id not in products:
                        line.unlink()
                ref._recompute_tax_lines()
                ref._compute_amount()

                account_id = self.env['account.account'].search(
                    [('code', '=', 410100),
                     ('company_id', '=', self.env.user.company_id.id)]
                )
                self.env['account.move.line'].create({
                    'product_id': pick.carrier_id.product_id.id,
                    'quantity': 1,
                    'price_unit': pick.total_import - ref.amount_total,
                    'name': pick.carrier_id.product_id.name,
                    'account_id': account_id.id,
                    'tax_ids': [
                        (6, False, [pick.carrier_id.product_id.taxes_id.ids])
                    ],
                    'move_id': ref.id
                })

                ref._recompute_tax_lines()
                ref._compute_amount()

        for can in cancel:
            can.invoice_ids.write({'state': 'cancel'})
            can.unlink()

        return super().action_cancel()

    def open_website_url(self):
        self.ensure_one()
        brt = self.env.ref('netaddiction_warehouse.carrier_brt').id

        if self.carrier_id.id == brt:
            url = 'http://as777.brt.it/vas/sped_det_show.hsm?referer=sped_numspe_par.htm&ChiSono=%s' % self.delivery_barcode
        else:
            url = 'https://www.mysda.it/SDAServiziEsterniWeb2/faces/SDAElencoSpedizioni.jsp?user=NETA20&idritiro=%s' % self.delivery_barcode

        return {
            'type': 'ir.actions.act_url',
            'name': "Shipment Tracking Page",
            'target': 'new',
            'url': url,
        }

    def _get_number_of_pieces(self):
        for pick in self:
            pieces = 0
            for line in pick.move_line_ids:
                pieces += line.qty_done
            pick.number_of_pieces = pieces

    def _get_total_import(self):
        for pick in self:
            total = 0.00
            pp_aj = self.env.ref('netaddiction_payments.paypal_journal')
            sf_aj = self.env.ref('netaddiction_payments.sofort_journal')
            if pick.payment_id \
                    and pick.payment_id.journal_id not in (pp_aj, sf_aj):
                pick.total_import = pick.payment_id.amount
                continue

            for line in pick.group_id.procurement_ids:
                total += line.sale_line_id.price_subtotal + line.sale_line_id.price_tax

            res = self.carrier_id.product_id.taxes_id.compute_all(
                self.carrier_price)

            total += res['total_included']

            method_contrassegno_id = self.env['ir.model.data'].get_object(
                'netaddiction_payments', 'contrassegno_journal').id

            if pick.sale_order_payment_method.id == method_contrassegno_id and not pick.sale_id.pronto_campaign:
                contrassegno = self.env.ref(
                    'netaddiction_payments.product_contrassegno')
                res_c = self.carrier_id.product_id.taxes_id.compute_all(
                    contrassegno.list_price)
                total += res_c['total_included']

            # TODO: gestione gift?
            # if pick.sale_id.gift_discount > 0.0:
            #     gift = self.env[
            #         "netaddiction.gift_invoice_helper"].compute_gift_value(
            #         self.sale_id.gift_discount, pick.sale_id.amount_total,
            #         total)
            #     total -= gift

            pick.total_import = total

    def pick_up_scraped(self, product_barcode, qty_to_down):
        wh_op_sett_obj = self.env['netaddiction.warehouse.operations.settings']
        scraped_type = wh_op_sett_obj.search(
            [('company_id', '=', self.env.user.company_id.id),
             ('netaddiction_op_type', '=', 'reverse_supplier_scraped')]
        )
        scrape_id = scraped_type.operation.id

        product_lines = []
        if self.picking_type_id.id == scrape_id:
            product_lines += [
                x
                for x in self.move_line_ids
                if x.product_id.barcode == product_barcode
            ]
        for line in product_lines:
            line.write({'qty_done': line.product_qty})

    def set_pick_up(self, product_barcode, shelf_id, qty_to_down):
        """
        per ogni stock picking eseguo
        """
        wh_op_sett_obj = self.env['netaddiction.warehouse.operations.settings']
        qty = 0
        for pick in self:
            product_lines = [
                x
                for x in pick.move_line_ids
                if x.product_id.barcode == product_barcode
            ]
            test = int(qty_to_down)

            for line in product_lines:
                shelf = wh_op_sett_obj.search(
                    [('product_id', '=', line.product_id.id),
                     ('wh_location_id', '=', int(shelf_id))]
                )
                if not shelf:
                    raise ValidationError("Ripiano inesistente")

                qty_line = int(line.product_qty) - int(line.qty_done)

                if test > 0:
                    if int(qty_line) <= test:
                        shelf.qty -= int(qty_line)
                        line.qty_done += float(qty_line)
                        test -= qty_line
                        qty += qty_line
                        qty_line = 0
                        if shelf.qty == 0:
                            shelf.unlink()
                    else:
                        shelf.qty -= int(test)
                        line.qty_done += float(test)
                        qty = qty + test
                        test = 0
                        if shelf.qty == 0:
                            shelf.unlink()

        return qty

    ##############################
    # END INVENTORY APP FUNCTION #
    ##############################

    @api.model
    def create_reverse(self, attr, order_id):
        resale = False
        if 'resale' in attr:
            resale = True
            attr.pop('resale', None)

        # INIZIO CREAZIONE NOTA DI CREDITO
        order = self.env['sale.order'].search([('id', '=', int(order_id))])

        pids = {}
        count = {}

        # si prende i prodotti e le quantità di ogni riga picking
        # segnata come reso
        for line in attr['move_line_ids']:
            pids[int(line[2]['product_id'])] = line[2]['product_qty']
            count[int(line[2]['product_id'])] = line[2]['product_qty']

        # trova le fatture per quell'ordine con quei prodotti
        invoices = self.env['account.move'].search(
            [('invoice_origin', '=', order.name),
             ('invoice_line_ids.product_id', 'in', list(pids.keys()))]
        )

        # per ogni riga fattura controlla che quel prodotto sia presente tra i
        # prodotti resi
        # Lavora le quantità in modo da poter modificare la nota di credito
        # creata con i dati corretti
        # in to_credit ritorna gli id delle fatture su cui effettuare le note di credito
        to_credit = []
        for inv in invoices:
            for line in inv.invoice_line_ids:
                if line.product_id.id in count:
                    if count[line.product_id.id] <= line.quantity:
                        to_credit.append(inv)
                        count.pop(line.product_id.id)
                    else:
                        to_credit.append(inv)
                        count[line.product_id.id] -= line.quantity
        to_credit = set(to_credit)

        # per ogni fattura trovata create la nota di credito in data odierna
        # analizza le righe fattura per correggere i dati dei prodotti con quelli estratti precedentemente
        for inv in to_credit:
            move = inv._reverse_moves()
            for line in move.invoice_line_ids:
                if pids.get(line.product_id.id, 0) > 0:
                    if pids[line.product_id.id] == line.quantity:
                        pids[line.product_id.id] = 0
                    elif pids[line.product_id.id] < line.quantity:
                        line.write({'quantity': pids[line.product_id.id]})
                        pids[line.product_id.id] = 0
                    else:
                        pids[line.product_id.id] -= line.quantity
                else:
                    line.unlink()
            move.invoice_origin = inv.number
        # FINE CREAZIONE NOTA DI CREDITO

        resi = self.env['netaddiction.wh.locations'].search(
            [('barcode', '=', '0000000002')]
        )

        picking = self.create(attr)
        picking.action_assign()
        for line in picking.move_line_ids:
            line.write({'qty_done': line.product_uom_qty})

        picking.action_confirm()

        moves = self.env['stock.move'].search(
            [('picking_id', '=', picking.id)]
        )
        moves.write({'origin': picking.origin})

        if resale:
            for line in picking.move_line_ids:
                self.env['netaddiction.wh.locations.line'].allocate(
                    line.product_id.id, int(line.product_uom_qty), resi.id
                )

    def create_supplier_reverse(self, products, supplier, operations):
        """
        crea i picking per il reso a fornitore.
        products è un oggetto passato dal client products
            {scraped:array[id:qta],commercial:array[id:qta]}
        supplier è l'id del fornitore a cui fare il reso.
        """
        supplier = self.env['res.partner'].search([('id', '=', int(supplier))])

        products = json.loads(products)
        operations = json.loads(operations)

        wh = operations['reverse_supplier']['default_location_src_id'][0]
        supp_wh = operations['reverse_supplier']['default_location_dest_id'][0]
        scraped_wh = operations['reverse_supplier_scraped']['default_location_src_id'][0]

        scrape_type = operations['reverse_supplier_scraped']['operation_type_id']
        commercial_type = operations['reverse_supplier']['operation_type_id']

        # prendo in esame i resi difettati
        pack_operation_scrapeds = []
        for prod in products['scraped']:
            line = (0, 0, {
                'product_id': int(prod['pid']),
                'product_uom_qty': int(prod['qta']),
                'location_id': int(scraped_wh),
                'location_dest_id': int(supp_wh),
                'product_uom_id': 1
            })
            pack_operation_scrapeds.append(line)

        # prendo in esame i resi commerciali
        pack_operation_commercial = []
        for prod in products['commercial']:
            line = (0, 0, {
                'product_id': int(prod['pid']),
                'product_uom_qty': int(prod['qta']),
                'location_id': int(wh),
                'location_dest_id': int(supp_wh),
                'product_uom_id': 1
            })
            pack_operation_commercial.append(line)

        # preparo gli attributi per il picking
        pick_scrape = {
            'partner_id': int(supplier),
            'origin': 'Reso a Fornitore Difettati %s' % supplier.name,
            'location_dest_id': int(supp_wh),
            'picking_type_id': scrape_type,
            'location_id': int(scraped_wh),
            'move_line_ids': pack_operation_scrapeds,
        }

        pick_commercial = {
            'partner_id': int(supplier),
            'origin': 'Reso a Fornitore Commerciali %s' % supplier.name,
            'location_dest_id': int(supp_wh),
            'picking_type_id': commercial_type,
            'location_id': int(wh),
            'move_line_ids': pack_operation_commercial,
        }

        ids = []
        if products['scraped']:
            scrape_picking = self.create([pick_scrape])
            scrape_picking.action_assign()
            scrape_picking.action_confirm()
            ids.append(scrape_picking.id)
        if products['commercial'] > 0:
            commercial_picking = self.create([pick_commercial])
            commercial_picking.action_assign()
            commercial_picking.action_confirm()
            ids.append(commercial_picking.id)

        batch = self.env['stock.picking.batch'].create({
            'name': 'Reso a Fornitore %s' % supplier.name,
            'picking_ids': [(6, 0, ids)],
            'reverse_supplier': True,
        })
        batch.write({'name': batch.name + ' - %s' % batch.id})
