# -*- coding: utf-8 -*-

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
import datetime

class Orders(models.Model):
    _inherit = 'sale.order'

    is_b2b = fields.Boolean(string="B2B")

    @api.multi
    def simulate_total_delivery_price(self, subdivision=None, option='all'):
        """
        Restituisce il costo totale delle spedizioni.
        """
        self.ensure_one()

        if not self.is_b2b:
            return super(Orders, self).simulate_total_delivery_price(subdivision, option)

        return 0

    @api.multi
    def simulate_delivery_price(self, subdivision):
        self.ensure_one()

        if not self.is_b2b:
            return super(Orders, self).simulate_delivery_price(subdivision)

    @api.onchange('partner_id')
    def _get_partner_data_b2b(self):
        if self.partner_id.is_b2b:
            self.delivery_option = 'asap'
            self.is_b2b = self.partner_id.is_b2b
            if self.partner_id.property_delivery_carrier_id:
                self.carrier_id = self.partner_id.property_delivery_carrier_id
            self.payment_method_id = self.partner_id.favorite_payment_method
        else:
            self.delivery_option = ''
            self.is_b2b = self.partner_id.is_b2b
            self.payment_method_id = False
            self.carrier_id = False

    @api.multi
    def set_delivery_price(self):
        if not self.is_b2b:
            return super(Orders, self).set_delivery_price()

    @api.multi
    def check_qty_limit_b2b(self):
        self.ensure_one()
        for line in self.order_line:
            pricelist_line = self.env['product.pricelist.item'].search([('product_id', '=', line.product_id.id), ('pricelist_id', '=', self.pricelist_id.id)])
            if pricelist_line:
                # qtà zero è zero, semmai deve essere negativa
                qty_limit = pricelist_line.qty_lmit_b2b
                if line.product_id.qty_available_now - line.product_uom_qty < qty_limit:
                    message = "Non puoi ordinare piu di %s pezzi per %s " % (line.product_id.qty_available_now + abs(pricelist_line.qty_lmit_b2b), line.product_id.display_name)
                    raise ProductB2BQuantityExceededException(self.id, line.product_id.qty_available_now, message)

    @api.multi
    def create_shipping(self):
        # per il b2b fa altri calcoli
        self.ensure_one()
        if not self.is_b2b:
            return super(Orders, self).create_shipping()

        self.check_qty_limit_b2b()

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order']

        results = self.order_line.simulate_shipping_b2b()
        for res in results:
            if res == 'available':
                name = "%s - %s" % (self.name, results[res]['date'])
                attr = {
                    'name': name,
                    'move_type': 'one',
                    'partner_id': self.partner_id.id
                }
                proc = self.env['procurement.group'].create(attr)
                delivery_date = results[res]['date']
                for line in results[res]['lines']:
                    if line.state != 'sale' or not line.product_id._need_procurement():
                        continue
                    qty = 0.0

                    for proc in line.procurement_ids:
                        qty += proc.product_qty
                    if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                        continue
                    vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)

                    planned = delivery_date - datetime.timedelta(days=int(self.carrier_id.time_to_shipping))

                    vals['date_planned'] = planned
                    vals['group_id'] = proc.id
                    new_proc = self.env["procurement.order"].create(vals)
                    new_procs += new_proc
            if res == 'not_available':
                for ship in results[res]:
                    name = "%s - %s %s" % (self.name, ship['date'], ship['lines'][0].id)
                    attr = {
                        'name': name,
                        'move_type': 'one',
                        'partner_id': self.partner_id.id
                    }
                    proc = self.env['procurement.group'].create(attr)
                    for line in ship['lines']:
                        delivery_date = ship['date']
                        if line.state != 'sale' or not line.product_id._need_procurement():
                            continue
                        qty = 0.0

                        for proc in line.procurement_ids:
                            qty += proc.product_qty
                        if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                            continue
                        vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)

                        planned = delivery_date - datetime.timedelta(days=int(self.carrier_id.time_to_shipping))

                        vals['date_planned'] = planned
                        vals['group_id'] = proc.id
                        new_proc = self.env["procurement.order"].create(vals)
                        new_procs += new_proc

        new_procs.run()
        return new_procs

class B2BOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def simulate_shipping_b2b(self):
        results = self.simulate_shipping(confirm_order=True)
        # tutti i prodotti che non sono disponibili creano singole spedizioni posticipate
        b2b_results = {'available': {'date': None, 'lines': []}, 'not_available': []}
        old_date = None
        for res in results:
            for line in results[res]:
                product = line['product_id']
                if product.days_available > 0:
                    b2b_results['not_available'].append({'date': res, 'lines': line})
                else:
                    if not old_date:
                        b2b_results['available']['date'] = res
                        b2b_results['available']['lines'].append(line)
                    elif res == old_date:
                        b2b_results['available']['date'] = res
                        b2b_results['available']['lines'].append(line)
                    else:
                        b2b_results['not_available'].append({'date': res, 'lines': line})
                old_date = res
        return b2b_results

class ProductB2BQuantityExceededException(Exception):
    def __init__(self, product_id, remains_quantity, err_str):
        super(ProductB2BQuantityExceededException, self).__init__(product_id)
        self.var_name = 'confirm_exception_product'
        self.err_str = err_str
        self.product_id = product_id
        self.remains_quantity = remains_quantity

        
    def __str__(self):
        s = u"Errore prodotto %s : %s " %(self.product_id, self.err_str)
        return s
    def __repr__(self):
        s = u"Errore prodotto %s : %s " %(self.product_id, self.err_str)
        return s