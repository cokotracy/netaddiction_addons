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

class Orders(models.Model):
    _inherit="sale.order"
    delivery_option = fields.Selection([('all', 'In una unica spedizione'), ('asap', 'Man mano che i prodotti sono disponibili')],
                                       string='Opzione spedizione')

    @api.multi
    def action_confirm(self):
        res = super(Orders,self).action_confirm()
        self.create_shipping()
        self.set_delivery_price()
        return res

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

        if not self.carrier_id:
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
                vals['date_planned'] = delivery_date
                vals['group_id'] = proc.id
                new_proc = self.env["procurement.order"].create(vals)
                new_procs += new_proc
        new_procs.run()

        pickings = self.env['stock.picking'].search([('origin','=',self.name)])
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
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        free_prod_ship = []
        if len(self.free_ship_prod)>0:
            #controlla le linee di spese gratis
            #ci vanno gli id dei prodotti
            for i in self.free_ship_prod:
                free_prod_ship.append(i.id)

        sped_vaucher = False
        if len(self.offers_vaucher)>0:
            for i in self.offers_vaucher:
                if i.offer_type == 3:
                    sped_vaucher = True

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

            if subtotal >= price_delivery_gratis or sped_vaucher or ship_gratis:
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
            self.env['sale.order.line'].create(values)

        self.write({'delivery_price' : total_ship})

        self.env.cr.commit()


    @api.multi
    def simulate_delivery_price(self,subdivision):
        """
        simula le spese di spedizione dovute
        a partire dall suddivisione in spedizioni
        """
        if not self.carrier_id:
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        free_prod_ship = []
        if len(self.free_ship_prod)>0:
            #controlla le linee di spese gratis
            #ci vanno gli id dei prodotti
            for i in self.free_ship_prod:
                free_prod_ship.append(i.id)

        sped_vaucher = False
        if len(self.offers_vaucher)>0:
            for i in self.offers_vaucher:
                if i.offer_type == 3:
                    sped_vaucher = True


        price_delivery_gratis = self.carrier_id.amount
        total_delivery_price = defaultdict(dict)
        for delivery_date in subdivision:
            subtotal = 0
            ship_gratis = False
            for line in subdivision[delivery_date]:
                subtotal += line['price_total']
                if line['product_id'].id in free_prod_ship:
                    ship_gratis = True

            if subtotal >= price_delivery_gratis or ship_gratis or sped_vaucher:
                total_delivery_price[delivery_date]['price'] = 0.00
                total_delivery_price[delivery_date]['price_taxed'] = 0.00
            else:
                total_delivery_price[delivery_date]['price'] = self.carrier_id.fixed_price
                total_delivery_price[delivery_date]['price_taxed'] = round(self.carrier_id.fixed_price * 1.22, 2)

        return total_delivery_price

    @api.multi
    def simulate_shipping(self):
        self.ensure_one()
        if not self.carrier_id:
            raise ValidationError("Deve essere scelto un metodo di spedizione")
        return self.order_line.simulate_shipping()


class SaleOrderLine(models.Model):

    _inherit="sale.order.line"

    @api.multi
    def simulate_shipping(self, confirm_order = False):
        """
        simile a check_number_delivery ma simula solo le posibili spedizioni
        """
        #dict di appoggio
        support = defaultdict(list)
        
        for line in self:
            if not line.is_delivery:
                if len(line.offer_cart_history) == 0 and len(line.offer_vaucher_history) == 0:
                    support['without_offer'] += [line] 
                else:
                    #ci sono delle offerte associate a questa linea
                    if len(line.offer_cart_history)>0:
                        support[line.offer_cart_history.offer_name].append(line)
                    elif len(line.offer_vaucher_history)>0:
                        support[line.offer_vaucher_history.offer_name].append(line) 

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

        this_moment = subdivision.keys()[0]
        definitive_sub = {}
        for date in subdivision:
            diff = (date - this_moment).days
            if diff <=1:
                if this_moment in definitive_sub.keys():
                    definitive_sub[date] = subdivision[date] + definitive_sub[this_moment]
                    del(definitive_sub[this_moment])
                else:
                    definitive_sub[date] = subdivision[date]
            else:
                definitive_sub[date] = subdivision[date]
                this_moment = date

        subdivision = OrderedDict(sorted(definitive_sub.items()))


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
            attr_now['price_subtotal'] = round(attr_now['price_unit'] * control_qty,2)
            attr_now['price_total'] = round(attr_now['price_subtotal'] * (1+attr_now['tax_id'].amount/100),2)
            attr_now['price_tax'] = round(attr_now['price_total'] - attr_now['price_subtotal'],2)

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
            attr['price_subtotal'] = round(attr['price_unit'] * diff,2)
            attr['price_total'] = round(attr['price_subtotal'] * (1+attr['tax_id'].amount/100),2)
            attr['price_tax'] = round(attr['price_subtotal'] - attr['price_subtotal'],2)

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
        delivery_date = self._check_line_shipping_date()
        if qty == 0:
            available_days = self.product_id.calculate_days_available(0)
            return delivery_date + datetime.timedelta(days=int(available_days))
        else:
            return delivery_date

    @api.multi
    def _check_line_shipping_date(self):
        """
        calcola l'ipotetica data di consegna prevista per la linea ordine
        """
        self.ensure_one()
        carrier_time = int(self.order_id.carrier_id.time_to_shipping)
        shipping_date = datetime.date.today() + datetime.timedelta(days=int(self.product_id.days_available)) + datetime.timedelta(days=carrier_time)            
        if int(shipping_date.strftime("%w")) == 0:
            shipping_date += datetime.timedelta(days=1) + datetime.timedelta(days=carrier_time)
        if int(shipping_date.strftime("%w")) == 6:
            shipping_date += datetime.timedelta(days=2) + datetime.timedelta(days=carrier_time)

        return shipping_date 

    @api.multi
    def _action_procurement_create(self):
        pass


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_barcode = fields.Char(string="Barcode Spedizione")

    ################################
    #FUNCTION PER CONTROLLO PICK UP#
    ################################
    @api.model
    def do_validate_orders(self,pick_id):
        this = self.search([('id','=',int(pick_id))])
        if this.check_backorder(this):
            wiz_id = self.env['stock.backorder.confirmation'].create({'pick_id': this.id})
            wiz_id.process()
            backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', this.id)])
            backorder_pick.write({'wave_id' : None})
        else:
            order = self.env['sale.order'].search([('name','=',this.origin)])
            order.action_done()

        this.do_new_transfer()
        count = self.search([('wave_id','=',this.wave_id.id),('state','not in',['draft','cancel','done'])])
        if len(count) == 0:
            this.wave_id.done()


    @api.multi
    def generate_barcode(self):
        """
        genera il barcode della spedizione
        """
        self.ensure_one()

        if 'Bartolini' in self.carrier_id.name:
            self.delivery_barcode = self._generate_barcode_bartolini()
        else:
            self.delivery_barcode = self._generate_barcode_sda()

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