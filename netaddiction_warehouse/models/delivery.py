# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from collections import defaultdict,OrderedDict
from openerp.exceptions import ValidationError
import datetime
import sys
import lib_holidays

class Orders(models.Model):
    _inherit="sale.order"
    delivery_option = fields.Selection([('all', 'In una unica spedizione'), ('asap', 'Man mano che i prodotti sono disponibili')],
                                       string='Opzione spedizione')

    @api.multi
    def action_confirm(self):

        if len(self.order_line) == 0:
            raise ValidationError("Devi inserire almeno un prodotto nell'ordine")

        if not self.env.context.get('no_check_limit_and_action', False):
            self.order_line.check_limit_and_action()

        self.pre_action_confirm()

        super(Orders,self).action_confirm()

        if len(self.picking_ids)==0:
            self.create_shipping()
            self.set_delivery_price()
            for pick in self.picking_ids:
                pick.generate_barcode()
        if not self.env.context.get('no_do_action_quantity', False):
            for line in self.order_line:
                line.product_id.do_action_quantity()   
        return True

    @api.multi
    def _compute_picking_ids(self):
        for order in self:
            picks = self.env['stock.picking'].search([('origin','=',order.name)])
            order.picking_ids = picks
            order.delivery_count = len(order.picking_ids)

    @api.multi
    def create_shipping(self):
        """
        Sostituisce _action_procurement_create di sale.order.line
        """
        self.ensure_one()
        holiday = lib_holidays.LibHolidays()
        if not self.carrier_id:
            #TODO: disattivare per importer
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order'] #Empty recordset

        if self.delivery_option == 'asap':
            delivery = self.order_line.simulate_shipping(confirm_order = True)
        else:
            delivery = {}
            test_delivery = self.order_line.simulate_shipping()
            max_date = max(test_delivery.keys())
            delivery[max_date] = self.order_line
        for delivery_date in delivery:
            #per prima cosa creo il procurement_group
            name = "%s - %s" % (self.name,delivery_date)
            proc = self.env['procurement.group'].search([('name','=',name)])
            if len(proc) == 0:
                attr = {
                    'name' : name,
                    'move_type' : 'one',
                    'partner_id' : self.partner_id.id
                }
                proc = self.env['procurement.group'].create(attr)
            
            for line in delivery[delivery_date]:
                if line.state != 'sale' or not line.product_id._need_procurement():
                    continue
                qty = 0.0

                for proc in line.procurement_ids:
                    qty += proc.product_qty
                if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                    continue
                vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)

                planned = delivery_date - datetime.timedelta(days=int(self.carrier_id.time_to_shipping))
                
                while holiday.is_holiday(planned):
                    planned -= datetime.timedelta(days = 1)

                vals['date_planned'] = planned
                vals['group_id'] = proc.id
                new_proc = self.env["procurement.order"].create(vals)
                new_procs += new_proc

        new_procs.run()

        self.env.cr.commit()
        return new_procs

    @api.multi
    def set_delivery_price(self):
        """
        setta le spese di spedizione per questo ordine dopo aver effettuato
        simulate_shipping()
        """
        self.ensure_one()

        if not self.carrier_id:
            #TODO: disattivare per importer
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        free_prod_ship = []
        if len(self.free_ship_prod)>0:
            #controlla le linee di spese gratis
            #ci vanno gli id dei prodotti
            for i in self.free_ship_prod:
                free_prod_ship.append(i.id)

        sped_voucher = False
        if len(self.offers_voucher)>0:
            for i in self.offers_voucher:
                if i.offer_type == 3:
                    sped_voucher = True

        price_delivery_gratis = self.carrier_id.amount
        total_delivery_price = {}

        for pick in self.picking_ids:
            #calcolo le spese base
            subtotal = 0
            ship_gratis = False
            for line in pick.group_id.procurement_ids:
                subtotal += line.sale_line_id.price_total
                if line.product_id.id in free_prod_ship:
                    ship_gratis = True

            if subtotal >= price_delivery_gratis or sped_voucher or ship_gratis:
                total_delivery_price[pick] = 0.00
            else:
                total_delivery_price[pick] = self.carrier_id.fixed_price
            
        total_ship = 0
        number_of_ship = 0
        taxes = self.carrier_id.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        for pick in total_delivery_price:
            total_ship += total_delivery_price[pick]
            number_of_ship += 1
            pick.write({'carrier_price' : total_delivery_price[pick]})
            values = {
                'order_id': self.id,
                'name': self.carrier_id.name,
                'product_uom_qty': 1,
                'product_uom': self.carrier_id.product_id.uom_id.id,
                'product_id': self.carrier_id.product_id.id,
                'price_unit': total_delivery_price[pick],
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
            }
            l = self.env['sale.order.line'].create(values)
            l.product_id_change()
            l.write({'price_unit': total_delivery_price[pick]})


        self.write({'delivery_price' : total_ship})

        self.env.cr.commit()


    @api.multi
    def simulate_total_delivery_price(self, subdivision=None):
        """
        Restituisce il costo totale delle spedizioni.
        """
        self.ensure_one()

        if subdivision is None:
            subdivision = self.simulate_shipping()

        prices = self.simulate_delivery_price(subdivision)

        return sum(prices.values())


    @api.multi
    def simulate_total_amount(self, delivery_price=None):
        """
        Restituisce il costo totale dell'ordine simulando il costo delle spedizioni.
        """
        self.ensure_one()

        if delivery_price is None:
            delivery_price = self.simulate_total_delivery_price()

        amount = self.amount_total + delivery_price
        amount -= self.compute_voucher_discount()

        return amount


    @api.multi
    def simulate_delivery_price(self,subdivision):
        """
        simula le spese di spedizione dovute
        a partire dalla suddivisione in spedizioni di simulate_shipping
        ritorna un dict con data => [prezzo,prezzo tassato]
        """
        if not self.carrier_id:
            #TODO: disattivare per importer
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        free_prod_ship = []
        if len(self.free_ship_prod)>0:
            #controlla le linee di spese gratis
            #ci vanno gli id dei prodotti
            for i in self.free_ship_prod:
                free_prod_ship.append(i.id)

        sped_voucher = False
        if len(self.offers_voucher)>0:
            for i in self.offers_voucher:
                if i.offer_type == 3:
                    sped_voucher = True


        price_delivery_gratis = self.carrier_id.amount
        total_delivery_price = {}
        for delivery_date in subdivision:
            subtotal = 0
            ship_gratis = False
            for line in subdivision[delivery_date]:
                subtotal += line['price_total']
                if line['product_id'].id in free_prod_ship:
                    ship_gratis = True

            if subtotal >= price_delivery_gratis or ship_gratis or sped_voucher:
                total_delivery_price[delivery_date] = 0.00
            else:
                value_tax = self.carrier_id.product_id.taxes_id.compute_all(self.carrier_id.fixed_price)
                total_delivery_price[delivery_date] = value_tax['total_included']
                # TODO: YURI NON CANCELLARE NELLE TUE CRISI MISTICHE DA PULIZIA
                # total_delivery_price[delivery_date] = self.carrier_id.fixed_price 

        return total_delivery_price

    @api.multi
    def simulate_shipping(self):
        """
        ritorna un dict con la data di presunta consegna e dentro 
        della roba simil order.line
        per sapere i costi di spedizione questo dict deve essere passato
        a simulate_delivery_price
        """
        self.ensure_one()
        if not self.carrier_id:
            #TODO: disattivare per importer
            raise ValidationError("Deve essere scelto un metodo di spedizione")
        return self.order_line.simulate_shipping()


class SaleOrderLine(models.Model):

    _inherit="sale.order.line"

    #controlla l'azione da fare sul prodotto al raggiungimento della qty disponibile
    @api.multi
    def check_limit_and_action(self):
        order_lines = {}
        for line in self:
            if line.product_id not in order_lines:
                order_lines[line.product_id] = 0
            order_lines[line.product_id] += line.product_qty
        
        for product in order_lines:
            product.check_quantity_product(order_lines[product])

            

    @api.multi
    def simulate_shipping(self, confirm_order = False):
        """
        simile a check_number_delivery ma simula solo le posibili spedizioni
        """
        #dict di appoggio
        support = defaultdict(list)
        
        for line in self:
            if not line.is_delivery:
                if len(line.offer_cart_history) == 0 and len(line.offer_voucher_history) == 0:
                    support['without_offer'] += [line] 
                else:
                    #ci sono delle offerte associate a questa linea
                    if len(line.offer_cart_history)>0:
                        support[line.offer_cart_history.offer_name].append(line)
                    elif len(line.offer_voucher_history)>0:
                        support[line.offer_voucher_history.offer_name].append(line) 

        return self._divide_lines(support, confirm_order)

    @api.model
    def _divide_lines(self,support,confirm_order = False):
        subdivision = defaultdict(list)
        previous_ids = []
        #do priorità alle linee senza offerta
        for line in support['without_offer']:
            data = line._get_shipping_information_data(previous_ids, confirm_order)
            previous_ids += [line.id]
            for dt in data:
                subdivision[dt] += data[dt]

        #le linee singole non mi interessano più
        del(support['without_offer'])
        for offer in support:
            support_date = []
            support_line = []
            support_ids_line = []
            for line in support[offer]:
                attr = line.dict_order_line()
                support_line += [attr]
                support_ids_line += [line]
                data = line._get_shipping_information_data(previous_ids)
                previous_ids += [line.id]
                for d in data:
                    support_date += [d]

            if confirm_order:
                subdivision[max(support_date)] += support_ids_line
            else:
                subdivision[max(support_date)] += support_line


        subdivision = OrderedDict(sorted(subdivision.items()))

        #this_moment = subdivision.keys()[0]
        #definitive_sub = {}
        #for date in subdivision:
        #    diff = (date - this_moment).days
        #    if diff <=1:
        #        if this_moment in definitive_sub.keys():
        #            definitive_sub[date] = subdivision[date] + definitive_sub[this_moment]
        #            del(definitive_sub[this_moment])
        #        else:
        #            definitive_sub[date] = subdivision[date]
        #    else:
        #        definitive_sub[date] = subdivision[date]
        #        this_moment = date
#
        #subdivision = OrderedDict(sorted(definitive_sub.items()))


        return subdivision


    @api.multi
    def _get_shipping_information_data(self,previous_ids, confirm_order = False):
        """
        controlla se ci sono altre linee con questo prodotto in previous_ids (e quindi già analizzate)
        si calcola l'intera quantità e valuta se questa linea può essere spedita o splittata
        e restituisce un dict con data : lista di dict simil sale.order.line (se sono più di uno allora la riga va splittata)
        """
        self.ensure_one()
        qty = 0
        previous_line = self.search([('product_id','=',self.product_id.id),('order_id','=',self.order_id.id),('id','in',previous_ids)])
        if len(previous_line) > 0:
            for line in previous_line:
                qty += line.product_qty

        #questa quantità serve a capire quante unità disponibili sono rimaste
        control_qty = self.product_id.qty_available_now - qty
        if control_qty <= 0:
            # non ho disponibilità, tutte le unità slittano
            delivery_date = self._get_delivery_date(0)
            attr = self.dict_order_line()
            if confirm_order:
                return {
                    delivery_date : [self]
                }

            return {
                delivery_date : [attr]
            }

        #ho ancora una certa disponibilità di unità
        if self.product_qty <= control_qty:
            #posso spedire tutto subito
            delivery_date = self._get_delivery_date(1)
            attr = self.dict_order_line()
            if confirm_order:
                return {
                    delivery_date : [self]
                }

            return {
                delivery_date : [attr]
            }
        else:
            #splitto la linea
            diff = self.product_qty - control_qty
            #la parte da spedire subito
            delivery_date_now = self._get_delivery_date(1)
            attr_now = self.dict_order_line()
            attr_now['product_qty'] = control_qty
            attr_now['product_uom_qty'] = control_qty

            tax_price = self.product_id.taxes_id.compute_all(self.price_unit)

            attr_now['price_subtotal'] = round(tax_price['total_excluded'] * control_qty,2)
            attr_now['price_total'] = round(tax_price['total_included'] * control_qty,2)
            diff_tax = tax_price['total_included'] - tax_price['total_excluded']
            attr_now['price_tax'] = round(diff_tax * control_qty,2)
            #attr_now['price_subtotal'] = round(attr_now['price_unit'] * control_qty,2)
            #attr_now['price_total'] = round(attr_now['price_subtotal'] * (1+attr_now['tax_id'].amount/100),2)
            #attr_now['price_tax'] = round(attr_now['price_total'] - attr_now['price_subtotal'],2)

            if confirm_order:
                self.write({
                    'product_uom_qty' : control_qty,
                    'product_qty' : control_qty
                    })
                self.product_id_change()
                line_now = self

            #la parte da spedire più avanti
            delivery_date = self._get_delivery_date(0)
            attr = self.dict_order_line()
            attr['product_qty'] = diff
            attr['product_uom_qty'] = diff
            #attr['price_subtotal'] = round(attr['price_unit'] * diff,2)
            #attr['price_total'] = round(attr['price_subtotal'] * (1+attr['tax_id'].amount/100),2)
            #attr['price_tax'] = round(attr['price_subtotal'] - attr['price_subtotal'],2)

            tax_price = self.product_id.taxes_id.compute_all(attr['price_unit'])
            attr_now['price_subtotal'] = round(tax_price['total_excluded'] * diff,2)
            attr_now['price_total'] = round(tax_price['total_included'] * diff,2)
            diff_tax = tax_price['total_included'] - tax_price['total_excluded']
            attr_now['price_tax'] = round(diff_tax * diff,2)

            if confirm_order:
                vals = {
                    'order_id' : attr['order_id'].id,
                    'product_id': attr['product_id'].id,
                    'product_qty' : diff,
                    'product_uom_qty' : diff,
                    'price_unit' : attr['price_unit'],
                    'product_uom' : attr['product_uom'].id,
                    'name' : attr['name'],
                    'tax_id' : [(4,attr['tax_id'].id,False)]
                }
                line_post = self.create(vals)
                

            if confirm_order:
                return {
                    delivery_date_now : [line_now],
                    delivery_date : [line_post]
                }

            return {
                delivery_date_now : [attr_now],
                delivery_date : [attr]
            }

    @api.multi
    def dict_order_line(self):
        """
        ritorna un dict simile alla orderline
        """
        self.ensure_one()
        return {
            'name' : self.name,
            'order_id' : self.order_id,
            'price_subtotal' : self.price_subtotal,
            'price_tax' : self.price_tax,
            'price_unit' : self.price_unit,
            'product_id' : self.product_id,
            'product_qty' : self.product_qty,
            'product_uom' : self.product_uom,
            'product_uom_qty' : self.product_uom_qty,
            'tax_id' : self.tax_id,
            'price_total' : self.price_total
        }

    @api.multi
    def _get_delivery_date(self,qty):
        """
        ritorna la probabile data di consegna
        se qty == 0 significa che non ho nulla disponibile
        se qty != 0 ho tutto disponibile
        """
        self.ensure_one()
        available_days = self.product_id.calculate_days_available(qty)
        delivery_date = self._check_line_shipping_date(available_days)
        return delivery_date
        #delivery_date = self._check_line_shipping_date()
        #if qty == 0:
        #    available_days = self.product_id.calculate_days_available(0)
        #    return delivery_date + datetime.timedelta(days=int(available_days))
        #else:
        #    return delivery_date

    @api.multi
    def _check_line_shipping_date(self,available_days):
        """
        calcola l'ipotetica data di consegna prevista per la linea ordine
        """
        self.ensure_one()
        carrier_time = int(self.order_id.carrier_id.time_to_shipping)
        shipping_days = self.product_id.calculate_days_shipping(available_days,carrier_time)
        #shipping_date = datetime.date.today() + datetime.timedelta(days=int(self.product_id.days_available)) + datetime.timedelta(days=carrier_time)            
        
        #if int(shipping_date.strftime("%w")) == 0:
        #    shipping_date += datetime.timedelta(days=1) + datetime.timedelta(days=carrier_time)
        #if int(shipping_date.strftime("%w")) == 6:
        #    shipping_date += datetime.timedelta(days=2) + datetime.timedelta(days=carrier_time)
        shipping_date = datetime.date.today() + datetime.timedelta(days=shipping_days)

        return shipping_date 

    @api.multi
    def _action_procurement_create(self):
        pass


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_barcode = fields.Char(string="Barcode Spedizione")
    delivery_read_manifest = fields.Boolean(string="Letto nel manifest",default="False")
    manifest = fields.Many2one(string="Manifest", comodel_name="netaddiction.manifest")

    date_of_shipping_home = fields.Date(string="Data di consegna" , compute = "_compute_date_of_shipping")

    #serie di campi computati che servono solo per l'autopreparazione
    sale_order_status = fields.Selection([
        ('draft', 'Nuovo'),
        ('sent', 'Preventivo Inviato'),
        ('sale', 'In Lavorazione'),
        ('partial_done', 'Parzialmente Completato'),
        ('problem', 'Problema'),
        ('done', 'Completato'),
        ('cancel', 'Annullato'),
    ], string='Stato Ordine', readonly=True, compute =  "_get_sale_order_status")

    sale_order_payment_method = fields.Many2one('account.journal', string='Metodo di pagamento', compute = "_get_sale_order_payment")

    @api.one 
    def _get_sale_order_status(self):
        self.sale_order_status = self.sale_id.state

    @api.one 
    def _get_sale_order_payment(self):
        self.sale_order_payment_method = self.sale_id.payment_method_id

    @api.one 
    def _compute_date_of_shipping(self):
        days = int(self.carrier_id.time_to_shipping)
        date_ship = datetime.datetime.strptime(self.min_date,'%Y-%m-%d %H:%M:%S') + datetime.timedelta(days = days)
        self.date_of_shipping_home = date_ship

    @api.multi
    def _add_delivery_cost_to_so(self):
        pass

    ################################
    #FUNCTION PER CONTROLLO PICK UP#
    ################################
    @api.model
    def do_validate_orders(self,pick_id):
        this = self.search([('id','=',int(pick_id))])

        #for pay in this.sale_id.account_payment_ids:
        #    if this.total_import == pay.amount and pay.state == 'posted'

        if this.check_backorder(this):
            wiz_id = self.env['stock.backorder.confirmation'].create({'pick_id': this.id})
            wiz_id.process()
            backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', this.id)])
            backorder_pick.write({'wave_id' : None})

        this.do_new_transfer()

        partial = False
        for pick in this.sale_id.picking_ids:
            if pick.state != 'done':
                partial=True

        if partial:
            this.sale_id.state='partial_done'
        else:
            this.sale_id.state='done'

        #a questo punto metto spedita e da fatturare anche la riga spedizioni 
        shipping_lines = self.env['sale.order.line'].search([('order_id','=',this.sale_id.id),
            ('price_unit','=',round(this.carrier_price,2)),('is_delivery','=',True),('qty_delivered','=',0)])
        if len(shipping_lines)>0:
            shipping_lines[0].write({
                'qty_delivered' : 1,
                'qty_to_invoice' : 1
                })

        count = self.search([('wave_id','=',this.wave_id.id),('state','not in',['draft','cancel','done'])])
        if len(count) == 0:
            this.wave_id.done()

        now = datetime.date.today()
        #cerco la presenza di un manifest
        manifest = self.env['netaddiction.manifest'].search([('date','=',now),('carrier_id','=',this.carrier_id.id)])
        if len(manifest)==0:
            #manifest per questo corriere non presente
            man_id = self.env['netaddiction.manifest'].create({'date':now,'carrier_id':this.carrier_id.id}).id
        else:
            man_id = manifest.id

        this.write({'manifest':man_id,'delivery_read_manifest':False})
        #fattura
        #new_invoices = this.sale_id.action_invoice_create()
        #sequenza fattura
        #sequence = self.env['ir.sequence'].search([('company_id','=',1),('name','ilike','Clienti')])
        #prefix = sequence.prefix
        #now = datetime.datetime.now()
        #next_number = 1
        #number = prefix.replace('%(range_year)s',str(datetime.date.today().year))

        #for line in sequence.date_range_ids:
        #    if datetime.datetime.strptime(line.date_from,'%Y-%m-%d') <= now and datetime.datetime.strptime(line.date_to,'%Y-%m-%d') >= now: 
        #        next_number = line.number_next
        #        number = prefix.replace('%(range_year)s',str(datetime.date.today().year))
        #        line.write({
        #                'number_next':int(line.number_next) + int(sequence.number_increment),
        #                'number_next_actual':int(line.number_next_actual) + int(sequence.number_increment)
        #            })
        #
        #prefix = sequence.prefix
        #fill = str(next_number).zfill(sequence.padding)

        #for i in new_invoices:
        #    this_inv = self.env['account.invoice'].search([('id','=',i)])
        #    this_inv.invoice_validate()
        #    this_inv.write({
        #        'number' : number + fill,
        #        'name' : number + fill,
        #        })

    @api.model
    def confirm_reading_manifest(self,pick):
        this = self.search([('id','=',int(pick))])

        #controllo che lo stato dell'ordine sia ancora completato
        if this.state != 'done':
            this.manifest = False
            return {'state' : 'problem', 'message' : 'L\'ordine è stato annullato'}

        this.delivery_read_manifest = True
        return {'state' : 'ok',}



    @api.multi
    def generate_barcode(self):
        """
        genera il barcode della spedizione
        """
        self.ensure_one()

        brt = self.env.ref('netaddiction_warehouse.carrier_brt').id

        if brt == self.carrier_id.id:
            self.delivery_barcode = self._generate_barcode_bartolini()
        else:
            self.delivery_barcode = self._generate_barcode_sda()

        self.carrier_tracking_ref = self.delivery_barcode
        self.env.cr.commit()

    @api.multi
    def _generate_barcode_bartolini(self):
        """
        creo un barcode univoco "nel mese"
        con prefix + idordine
        """
        self.ensure_one()
        
        prefix = 'CC0271'

        string = str(self.id).zfill(9)

        return prefix + string

    @api.multi
    def _generate_barcode_sda(self):
        return str(self.id).zfill(13)

    @api.model
    def do_multi_validate_orders(self,picks):
        for p in picks:
            self.do_validate_orders(p)

class deliveryCarrier(models.Model):
    _inherit="delivery.carrier"

    time_to_shipping = fields.Integer(string="Tempo di Consegna",default="1")

class Supplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    @api.onchange('name')
    def search_timing(self):
        self.delay = self.name.supplier_delivery_time

class StockMove(models.Model):

    _inherit = 'stock.move'

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the moves and if all moves are cancelled it cancels the picking.
        @return: True
        """
        procurement_obj = self.pool.get('procurement.order')
        context = context or {}
        procs_to_check = set()
        for move in self.browse(cr, uid, ids, context=context):
            #if move.state == 'done':
            #    raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
            if move.reserved_quant_ids:
                self.pool.get("stock.quant").quants_unreserve(cr, uid, move, context=context)
            if context.get('cancel_procurement'):
                if move.propagate:
                    procurement_ids = procurement_obj.search(cr, uid, [('move_dest_id', '=', move.id)], context=context)
                    procurement_obj.cancel(cr, uid, procurement_ids, context=context)
            else:
                if move.move_dest_id:
                    if move.propagate:
                        self.action_cancel(cr, uid, [move.move_dest_id.id], context=context)
                    elif move.move_dest_id.state == 'waiting':
                        #If waiting, the chain will be broken and we are not sure if we can still wait for it (=> could take from stock instead)
                        self.write(cr, uid, [move.move_dest_id.id], {'state': 'confirmed'}, context=context)
                if move.procurement_id:
                    # Does the same as procurement check, only eliminating a refresh
                    procs_to_check.add(move.procurement_id.id)

        res = self.write(cr, uid, ids, {'state': 'cancel', 'move_dest_id': False}, context=context)
        if procs_to_check:
            procurement_obj.check(cr, uid, list(procs_to_check), context=context)
        return res

