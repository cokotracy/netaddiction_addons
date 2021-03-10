import datetime

from collections import defaultdict
from itertools import chain
import pdb

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

from ..tools.lib_holidays import is_holiday


class Orders(models.Model):
    _inherit = 'sale.order'

    count_reverse = fields.Integer(
        compute='_count_reverse',
        string="# Resi",
    )

    delivery_option = fields.Selection(
        [('all', 'In una unica spedizione'),
         ('asap', 'Man mano che i prodotti sono disponibili')],
        string="Opzione spedizione"
    )

    # nuovo field inserito principalmente per le spedizioni di amazon: se
    # questo campo è > 0.0 le spedizioni costeranno quanto il valore del
    # campo, anche se secondo le logiche di multiplayer.com (vaucher, offerte)
    # avrebbero un altro costo.
    # NB NON VIENE VISUALIZZATO NEL SIMULATE SHIPPING
    # NB2 SE IL PRODOTTO SPEDIZIONE FOSSE SOGGETTO A UNA OFFERTA CATALOGO
    # (COSA ERRATA) ``delivery_desired_price`` NON FUNZIONEREBBE
    delivery_desired_price = fields.Float(
        default=0.0,
        string="Prezzo desiderato per la spedizione",
    )

    is_reversible = fields.Boolean(
        compute='is_reversible_func',
        string="Reversibile",
    )

    def get_reverse_pickings(self):
        """
        Si prende i settings per i resi ['reverse_scrape','reverse_resale']
        Trova tutte le tipologie di picking per questi settings
        Ritorna i picking collegati a queste tipologie e all'ordine corrente
        """
        self.ensure_one()
        company_id = self.env.user.company_id.id
        reverse_op_types = ['reverse_scrape', 'reverse_resale']
        sett = self.env['netaddiction.warehouse.operations.settings'].search(
            [('netaddiction_op_type', 'in', reverse_op_types),
             ('company_id', '=', company_id)]
        )
        picking_types = sett.mapped('operation')
        return self.env['stock.picking'].search([
            ('origin', '=', self.name),
            ('picking_type_id', 'in', picking_types.ids)
        ])

    def _count_reverse(self):
        """
        Si prende i settings per i resi ['reverse_scrape','reverse_resale']
        Trova tutti i picking effettuati per queste tipologie
        Li conta e aggiorna count_reverse
        """
        for order in self:
            order.count_reverse = len(order.get_reverse_pickings().ids)

    def is_reversible_func(self):
        """
        Prende tutti i resi per questo sale.order.
        Ogni riga reso lo confronta con le righe ordine e per ogni riga estrae
        le quantità di quel prodotto da poter ancora rendere.
        Se la quantità da poter rendere è maggiore di zero allora ritorna True
        """
        for order in self:
            pickings = order.get_reverse_pickings()
            pick_pids = defaultdict(float)
            for pick in pickings:
                for line in pick.move_line_ids:
                    if line.product_id.id in pick_pids:
                        pick_pids[line.product_id.id] += line.qty_done
                    else:
                        pick_pids[line.product_id.id] = line.qty_done

            to_reverse = defaultdict(float)
            for line in order.order_line:
                if line.product_id.id in pick_pids:
                    qta = line.qty_delivered - pick_pids[line.product_id.id]
                    if qta > 0:
                        if line.product_id.id in to_reverse:
                            to_reverse[line.product_id.id] += qta
                        else:
                            to_reverse[line.product_id.id] = qta
                else:
                    if line.qty_delivered > 0:
                        to_reverse[line.product_id.id] = line.qty_delivered

            order.is_reversible = bool(to_reverse)

    #action view per i resi
    def open_reverse(self):
        self.ensure_one()
        pickings = self.get_reverse_pickings()
        view_id = self.env['ir.ui.view'].search([('name','=','stock.vpicktree')])
        return {
            'type': 'ir.actions.act_window',
            'res_model': "stock.picking",
            'view_id': view_id.id,
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', pickings.ids)],
            'context': {},
            'name': 'Resi per ordine %s' % self.name
        }

    def get_payment(self):
        """
        ritorna il metodo di pagamento usato o presunto dal pagamento
        dipende strettamente da netaddiction_payments
        """
        self.ensure_one()

        if len(self.account_payment_ids) > 0:
            return self.account_payment_ids[0]

        return False

    def action_confirm(self):
        for order in self:
            if order.state not in ('draft', 'pending', 'problem'):
                # se lo stato non  è draft è già stata chiamata action confirm
                continue

            if not order.order_line:
                raise ValidationError(
                    "Devi inserire almeno un prodotto nell'ordine"
                )

            '''
            TODO: Check if we need it, again
            if not self.env.context.get('no_check_limit_and_action', False):
                if not order.parent_order:
                    order.order_line.check_limit_and_action()
            '''

        res = super().action_confirm()

        for order in self:
            if not order.picking_ids:
                order.create_shipping()
                order.set_delivery_price()
                for pick in order.picking_ids:
                    pick.generate_barcode()
            if not self.env.context.get('no_do_action_quantity', False):
                for line in order.order_line:
                    if not order.parent_order:
                        line.product_id.do_action_quantity()

        return res

    def _compute_picking_ids(self):
        for order in self:
            picks = self.env['stock.picking'].search(
                [('origin', '=', order.name)]
            )
            order.picking_ids = picks
            order.delivery_count = len(order.picking_ids)

    def create_shipping(self):
        """
        Sostituisce _action_procurement_create di sale.order.line
        """
        self.ensure_one()
        if not self.carrier_id \
                and not self.env.context.get('skin_carrier_check', False):
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        new_procs = self.env['procurement.order']  # Empty recordset
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure'
        )

        if self.delivery_option == 'asap':
            delivery = self.order_line.simulate_shipping(confirm_order=True)
        else:
            delivery = {}
            test_delivery = self.order_line.simulate_shipping()
            max_date = max(test_delivery.keys())
            delivery[max_date] = self.order_line
        for delivery_date in delivery:
            # per prima cosa creo il procurement_group
            name = "%s - %s" % (self.name, delivery_date)
            proc = self.env['procurement.group'].search([('name', '=', name)])
            if not proc:
                proc = self.env['procurement.group'].create({
                    'name': name,
                    'move_type': 'one',
                    'partner_id': self.partner_id.id
                })

            for line in delivery[delivery_date]:
                if line.state != 'sale' \
                        or not line.product_id._need_procurement():
                    continue

                qty = 0.0
                for proc in line.procurement_ids:
                    qty += proc.product_qty
                if float_compare(qty, line.product_uom_qty, precision) >= 0:
                    continue
                vals = line._prepare_order_line_procurement(
                    group_id=line.order_id.procurement_group_id.id
                )

                planned = delivery_date - datetime.timedelta(
                    days=int(self.carrier_id.time_to_shipping)
                )

                while is_holiday(planned):
                    planned -= datetime.timedelta(days=1)

                vals['date_planned'] = planned
                vals['group_id'] = proc.id
                new_proc = self.env["procurement.order"].create(vals)
                new_procs += new_proc

        new_procs.run()
        return new_procs

    def set_delivery_price(self):
        """
        setta le spese di spedizione per questo ordine dopo aver effettuato
        simulate_shipping()
        """
        self.ensure_one()

        if not self.carrier_id \
                and not self.env.context.get('skin_carrier_check', False):
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        free_prod_ship = self.free_ship_prod.ids

        sped_voucher = False
        if self.offers_voucher:
            sped_voucher = any(i.offer_type == 3 for i in self.offers_voucher)

        price_delivery_gratis = self.carrier_id.amount
        total_delivery_price = {}

        for pick in self.picking_ids:
            # calcolo le spese base
            subtotal = 0
            ship_gratis = False
            for line in pick.group_id.procurement_ids:
                subtotal += line.sale_line_id.price_total
                if line.product_id.id in free_prod_ship:
                    ship_gratis = True

            if subtotal >= price_delivery_gratis \
                    or sped_voucher \
                    or ship_gratis:
                total_delivery_price[pick] = 0.00
            else:
                total_delivery_price[pick] = self.carrier_id.fixed_price

        total_ship = 0
        number_of_ship = 0
        taxes = self.carrier_id.product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id
        )
        taxes_ids = taxes.ids
        for pick in total_delivery_price:
            if float_compare(self.delivery_desired_price, 0.0, 4) <= 0:
                price = total_delivery_price[pick]
            else:
                price = self.delivery_desired_price
            total_ship += price
            number_of_ship += 1
            pick.write({'carrier_price': price})
            values = {
                'order_id': self.id,
                'name': self.carrier_id.name,
                'product_uom_qty': 1,
                'product_uom': self.carrier_id.product_id.uom_id.id,
                'product_id': self.carrier_id.product_id.id,
                'price_unit': price,
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
            }
            so_line = self.env['sale.order.line'].create(values)
            so_line.product_id_change()
            so_line.write({'price_unit': price})

        self.write({'delivery_price': total_ship})

    def simulate_total_delivery_price(
        self, asap_subdivision=None, option='asap'
    ):
        """
        Restituisce il costo totale delle spedizioni.
        """
        self.ensure_one()

        if asap_subdivision is None:
            asap_subdivision = self.simulate_shipping()

        if option == 'asap':
            subdivision = asap_subdivision
        elif option == 'all':
            max_date = max(asap_subdivision.keys())
            subdivision = {
                max_date: list(
                    chain.from_iterable(list(asap_subdivision.values()))
                ),
            }

        prices = self.simulate_delivery_price(subdivision)

        return sum(prices.values())

    def simulate_total_amount(self, delivery_price=None):
        """
        Restituisce il costo totale dell'ordine simulando il costo delle
        spedizioni.
        """
        self.ensure_one()

        amount = self.amount_total

        if not self.partner_id.is_b2b:
            if delivery_price is None:
                delivery_price = self.simulate_total_delivery_price(
                    option=self.delivery_option
                )

            amount += delivery_price

        return amount

    def simulate_delivery_price(self, subdivision):
        """
        simula le spese di spedizione dovute
        a partire dalla suddivisione in spedizioni di simulate_shipping
        ritorna un dict con data => [prezzo,prezzo tassato]
        """
        if not self.carrier_id \
                and not self.env.context.get('skin_carrier_check', False):
            raise ValidationError("Deve essere scelto un metodo di spedizione")

        free_prod_ship = self.free_ship_prod.ids

        sped_voucher = False
        if self.offers_voucher:
            sped_voucher = any(i.offer_type == 3 for i in self.offers_voucher)

        price_delivery_gratis = self.carrier_id.amount
        delivery_prices = {}
        for delivery_date in subdivision:
            subtotal = 0
            ship_gratis = False
            for line in subdivision[delivery_date]:
                subtotal += line['price_total']

                if line['product_id'].id in free_prod_ship:
                    ship_gratis = True

            if subtotal >= price_delivery_gratis \
                    or ship_gratis \
                    or sped_voucher:
                delivery_prices[delivery_date] = 0.00
            else:
                value_tax = self.carrier_id.product_id.taxes_id.compute_all(
                    self.carrier_id.fixed_price
                )
                delivery_prices[delivery_date] = value_tax['total_included']
                # TODO: YURI NON CANCELLARE NELLE TUE CRISI MISTICHE DA PULIZIA
                # delivery_prices[delivery_date] = self.carrier_id.fixed_price
        return delivery_prices

    def simulate_shipping(self):
        """
        ritorna un dict con la data di presunta consegna e dentro
        della roba simil order.line
        per sapere i costi di spedizione questo dict deve essere passato
        a simulate_delivery_price
        """
        self.ensure_one()
        if not self.carrier_id \
                and not self.env.context.get('skin_carrier_check', False):
            raise ValidationError("Deve essere scelto un metodo di spedizione")
        return self.order_line.simulate_shipping()
