# -*- coding: utf-8 -*-

from openerp import models, api
import datetime
from openerp.exceptions import Warning

class PickingStats(models.Model):
    _inherit = "stock.picking"

    @api.model
    def get_picking_period(self, date_start, date_finish, states):
        # ritorna un recordset di stock.picking nel periodo in questi stati
        # date_start e date_finish devono essere delle string es: '2016-10-10' senza orario
        available_states = ['draft', 'cancel', ' confirmed', 'partially_available', 'assigned', 'done']
        for s in states:
            if s not in available_states:
                raise Warning("Hai inserito uno stato inesistente per la spedizione: %s" % s)

        date_start += ' 00:00:00'
        date_finish += ' 23:59:59'
        domain = [('state', 'in', states), ('date_done', '>=', date_start), ('date_done', '<=', date_finish)]

        results = self.search(domain)

        return results

    @api.multi
    def get_data_structure(self, groups):
        # dato un recordset estrae i dati in base a groups
        # groups è una lista di valori per cui raggruppare
        # ['state', 'payment_method_id', 'is_b2b', 'month', 'day']
        # ritorna la struttura dati per le statistiche
        datas = {
            'sale_order_payment_method': [],
            'date_start': False,
            'date_finish': False,
            'states': [],
            'operation_type': []
        }
        for pick in self:
            datas['sale_order_payment_method'].append(pick.sale_order_payment_method.name)
            datas['states'].append(pick.state)
            datas['operation_type'].append(pick.picking_type_id.name)
            date_done = datetime.datetime.strptime(pick.date_done, '%Y-%m-%d %H:%M:%S')
            if not datas['date_start']:
                datas['date_start'] = date_done
            if not datas['date_finish']:
                datas['date_finish'] = date_done
            if date_done < datas['date_start']:
                datas['date_start'] = date_done
            if date_done < datas['date_start']:
                datas['date_finish'] = date_done

        datas['sale_order_payment_method'] = set(datas['sale_order_payment_method'])
        datas['states'] = set(datas['states'])
        datas['operation_type'] = set(datas['operation_type'])
        return self._generate_data_structure(groups, states=datas['states'], date_start=datas['date_start'].strftime('%Y-%m-%d'),
            date_finish=datas['date_finish'].strftime('%Y-%m-%d'), sale_order_payment_method=datas['sale_order_payment_method'], operation_type=datas['operation_type'])

    @api.model
    def _generate_data_structure(self, groups, states=None, date_start=None, date_finish=None, sale_order_payment_method=None, operation_type=None):
        # crea la struttura dati che serve a raccogliere le statistiche degli ordini
        # groups è una lista di valori per cui raggruppare
        # ['state', 'payment_method_id', 'is_b2b', 'month', 'day', 'operation_type']
        # states ['sale', 'done', 'partial_done', 'cancel', 'pending', 'draft', 'problem']:
        # inizializzato solo se 'state' è presente in groups
        # date_start e date_finish devono essere delle string es: '2016-10-10' senza orario:
        # inizializzato solo se 'month' o 'day' sono in groups
        # payment_method_id sono i nomi dei metodi di pagamento
        orders = {
            'total': {
                'count': 0,
                'amount_total': 0,
                'margin': 0,
                'picking_ids': []
            }
        }

        if len(groups) == 0:
            return orders

        if 'month' in groups and (date_start is None or date_finish is None):
            raise Warning("date_start o date_finish devo essere inizializzati se 'month' è presente in groups")
        if 'day' in groups and (date_start is None or date_finish is None):
            raise Warning("date_start o date_finish devo essere inizializzati se 'month' è presente in groups")
        if 'state' in groups and states is None:
            raise Warning("states deve essere inizializzato se 'state' è presente in groups")
        if 'sale_order_payment_method' in groups and sale_order_payment_method is None:
            raise Warning("sale_order_payment_method deve essere inizializzato se 'sale_order_payment_method' è presente in groups")

        for g in groups:
            orders[g] = {}
            if g == 'state':
                for s in states:
                    orders[g][s] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'picking_ids': []
                    }
            if g == 'sale_order_payment_method':
                for j in sale_order_payment_method:
                    orders[g][j] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'picking_ids': []
                    }
            if g == 'is_b2b':
                orders[g][True] = {
                    'count': 0,
                    'amount_total': 0,
                    'margin': 0,
                    'picking_ids': []
                }
                orders[g][False] = {
                    'count': 0,
                    'amount_total': 0,
                    'margin': 0,
                    'picking_ids': []
                }
            if g == 'month':
                start = int(datetime.datetime.strptime(date_start, '%Y-%m-%d').strftime('%m'))
                finish = int(datetime.datetime.strptime(date_finish, '%Y-%m-%d').strftime('%m'))
                while start <= finish:
                    orders[g][start] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'picking_ids': []
                    }
                    start += 1
            if g == 'day':
                start = datetime.datetime.strptime(date_start, '%Y-%m-%d')
                finish = datetime.datetime.strptime(date_finish, '%Y-%m-%d')
                while start <= finish:
                    orders[g][start] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'picking_ids': []
                    }
                    start = start + datetime.timedelta(days=1)
            if g == 'operation_type':
                for op in operation_type:
                    orders[g][op] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'picking_ids': []
                    }

        return orders

    @api.multi
    def get_stats(self, groups, important_groups=None):
        # ritorna le statistiche
        # important_groups è una lista come groups che permette di suddividere ulteriormente i gruppi qui inseriti
        # se None important_groups viene ignorato
        orders = self.get_data_structure(groups)

        for res in self:
            orders['total']['count'] += 1
            orders['total']['amount_total'] += round(res.total_import, 2)
            orders['total']['amount_total'] = round(orders['total']['amount_total'], 2)
            orders['total']['picking_ids'].append(res.id)
            for g in groups:
                attr = False
                if g == 'month':
                    attr = int(datetime.datetime.strptime(res.date_done, '%Y-%m-%d %H:%M:%S').strftime('%m'))

                if g == 'day':
                    attr = datetime.datetime.strptime(res.date_done, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    attr = datetime.datetime.strptime(attr, '%Y-%m-%d')

                if g == 'is_b2b':
                    attr = res.sale_id.is_b2b

                if g == 'sale_order_payment_method':
                    attr = res.sale_order_payment_method.name

                if g == 'state':
                    attr = res.state

                if g == 'operation_type':
                    attr = res.picking_type_id.name

                orders[g][attr]['count'] += 1
                orders[g][attr]['amount_total'] += round(res.total_import, 2)
                orders[g][attr]['amount_total'] = round(orders[g][attr]['amount_total'], 2)
                orders[g][attr]['picking_ids'].append(res.id)

        if important_groups:
            for o in orders:
                if o != 'total':
                    for i in orders[o]:
                        if 'picking_ids' in orders[o][i]:
                            record = self.search([('id', 'in', orders[o][i]['picking_ids'])])
                            orders[o][i]['subdivision'] = record.get_stats(important_groups)

        return orders

    @api.multi
    def get_margin(self):
        products_cost = self.get_products_cost()
        products_cost['total']['total_sell_price'] = 0
        products_cost['total']['total_margin'] = 0
        products_cost['total']['categories'] = {}
        for pick in products_cost:
            if type(pick) is not str:
                products_cost[pick]['total_margin'] = 0
                products_cost[pick]['total_sell_price'] = 0
                products_cost[pick]['categories'] = {}
                for line in pick.sale_id.order_line:
                    if line.product_id in products_cost[pick]['products'].keys():
                        products_cost[pick]['products'][line.product_id]['sell_price'] += line.price_subtotal
                        products_cost[pick]['products'][line.product_id]['sell_price'] = round(products_cost[pick]['products'][line.product_id]['sell_price'], 2)
                        products_cost[pick]['total_sell_price'] += line.price_subtotal

                for pid in products_cost[pick]['products']:
                    products_cost[pick]['products'][pid]['margin'] = products_cost[pick]['products'][pid]['sell_price'] - products_cost[pick]['products'][pid]['cost']
                    products_cost[pick]['products'][pid]['margin'] = round(products_cost[pick]['products'][pid]['margin'], 2)
                    if pid.categ_id.name in products_cost['total']['categories'].keys():
                        products_cost['total']['categories'][pid.categ_id.name]['margin'] += products_cost[pick]['products'][pid]['margin']
                    else:
                        products_cost['total']['categories'][pid.categ_id.name] = {'margin': products_cost[pick]['products'][pid]['margin']}

                    if pid.categ_id.name in products_cost[pick]['categories'].keys():
                        products_cost[pick]['categories'][pid.categ_id.name]['total_margin'] += products_cost[pick]['products'][pid]['margin']
                    else:
                        products_cost[pick]['categories'][pid.categ_id.name] = {'total_margin': products_cost[pick]['products'][pid]['margin']}

                products_cost[pick]['total_margin'] += (products_cost[pick]['total_sell_price'] - products_cost[pick]['total_cost'])
                products_cost[pick]['total_margin'] = round(products_cost[pick]['total_margin'], 2)
                products_cost[pick]['total_sell_price'] = round(products_cost[pick]['total_sell_price'], 2)

                products_cost['total']['total_sell_price'] += products_cost[pick]['total_sell_price']
                products_cost['total']['total_sell_price'] = round(products_cost['total']['total_sell_price'], 2)
                products_cost['total']['total_margin'] += products_cost[pick]['total_margin']
                products_cost['total']['total_margin'] = round(products_cost['total']['total_margin'], 2)

        return products_cost

    @api.multi
    def get_products_cost(self):
        # PS: NON CALCOLA I CONTRIBUTI (SOLO LA RIVALUTAZIONE SE INSERITA)
        # tramite le move_lines trova la quant spostata
        # valorizza i prodotti
        # products è un dict con product.product e somma quantità per stock_picking
        # se products[stock_picking] è vuota allora non può recuperare il costo
        # se la spedizione è assigned vede il valore medio del prodotto in magazzino
        # se non è done o assigned calcola sul valore medio di acquisto dai fornitori
        products = {'total': {'total_cost': 0}}
        for pick in self:
            products[pick] = {'total_cost': 0, 'products': {}}
            for move in pick.move_lines:
                if move.state == 'done':
                    for quant in move.quant_ids:
                        products[pick]['total_cost'] += quant.inventory_value
                        products['total']['total_cost'] += quant.inventory_value
                        products['total']['total_cost'] = round(products['total']['total_cost'], 2)
                        if quant.product_id in products[pick]['products']:
                            products[pick]['products'][quant.product_id]['qty'] += quant.qty
                            products[pick]['products'][quant.product_id]['cost'] += quant.inventory_value
                        else:
                            products[pick]['products'][quant.product_id] = {
                                'qty': quant.qty,
                                'cost': quant.inventory_value,
                                'sell_price': 0,
                                'margin': 0
                            }
                        products[pick]['products'][quant.product_id]['cost'] = round(products[pick]['products'][quant.product_id]['cost'], 2)
                        products[pick]['total_cost'] = round(products[pick]['total_cost'], 2)

                if move.state == 'assigned':
                    medium_val = move.product_id.med_inventory_value * move.product_uom_qty
                    products[pick]['total_cost'] += medium_val
                    products['total']['total_cost'] += medium_val
                    products['total']['total_cost'] = round(products['total']['total_cost'], 2)
                    if move.product_id in products[pick]['products']:
                        products[pick]['products'][move.product_id]['qty'] += move.product_uom_qty
                        products[pick]['products'][move.product_id]['cost'] += medium_val
                    else:
                        products[pick]['products'][move.product_id] = {
                            'qty': move.product_uom_qty,
                            'cost': medium_val,
                            'sell_price': 0,
                            'margin': 0
                        }
                    products[pick]['products'][move.product_id]['cost'] = round(products[pick]['products'][move.product_id]['cost'], 2)
                    products[pick]['total_cost'] = round(products[pick]['total_cost'], 2)

                if move.state == 'confirmed' or move.state == 'waiting':
                    # prendo il valore medio dei fornitori
                    total = 0
                    nume = 0
                    for seller in move.product_id.seller_ids:
                        total += seller.price
                        nume += 1
                    medium_val = total / nume
                    medium_val = round(medium_val * move.product_uom_qty, 2)
                    products[pick]['total_cost'] += medium_val
                    products['total']['total_cost'] += medium_val
                    products['total']['total_cost'] = round(products['total']['total_cost'], 2)
                    if move.product_id in products[pick]['products']:
                        products[pick]['products'][move.product_id]['qty'] += move.product_uom_qty
                        products[pick]['products'][move.product_id]['cost'] += medium_val
                    else:
                        products[pick]['products'][move.product_id] = {
                            'qty': move.product_uom_qty,
                            'cost': medium_val,
                            'sell_price': 0,
                            'margin': 0
                        }
                    products[pick]['products'][move.product_id]['cost'] = round(products[pick]['products'][move.product_id]['cost'], 2)
                    products[pick]['total_cost'] = round(products[pick]['total_cost'], 2)

        return products
