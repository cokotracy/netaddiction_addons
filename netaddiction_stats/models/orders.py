# -*- coding: utf-8 -*-

from openerp import models, api
import datetime
from openerp.exceptions import Warning

class OrdersStats(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_orders_period(self, date_start, date_finish, states):
        # ritorna un recordset di ordini nel periodo in questi stati
        # date_start e date_finish devono essere delle string es: '2016-10-10' senza orario
        available_states = ['sale', 'done', 'partial_done', 'cancel', 'pending', 'draft', 'problem']
        for s in states:
            if s not in available_states:
                raise Warning("Hai inserito uno stato inesistente per l'ordine: %s" % s)

        date_start += ' 00:00:00'
        date_finish += ' 23:59:59'
        domain = [('state', 'in', states), ('date_order', '>=', date_start), ('date_order', '<=', date_finish)]
        results = self.search(domain)

        return results

    @api.multi
    def get_data_structure(self, groups):
        # dato un recordset estrae i dati in base a groups
        # groups è una lista di valori per cui raggruppare
        # ['state', 'payment_method_id', 'is_b2b', 'month', 'day']
        # ritorna la struttura dati per le statistiche
        datas = {
            'payment_method_id': [],
            'date_start': False,
            'date_finish': False,
            'states': [],
        }
        for order in self:
            datas['payment_method_id'].append(order.payment_method_id.name)
            datas['states'].append(order.state)
            date_order = datetime.datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S')
            if not datas['date_start']:
                datas['date_start'] = date_order
            if not datas['date_finish']:
                datas['date_finish'] = date_order
            if date_order < datas['date_start']:
                datas['date_start'] = date_order
            if date_order < datas['date_start']:
                datas['date_finish'] = date_order

        datas['payment_method_id'] = set(datas['payment_method_id'])
        datas['states'] = set(datas['states'])
        return self._generate_data_structure(groups, states=datas['states'], date_start=datas['date_start'].strftime('%Y-%m-%d'),
            date_finish=datas['date_finish'].strftime('%Y-%m-%d'), payment_method_id=datas['payment_method_id'])

    @api.multi
    def get_stats(self, groups, important_groups=None):
        # ritorna le statistiche
        # important_groups è una lista come groups che permette di suddividere ulteriormente i gruppi qui inseriti
        # se None important_groups viene ignorato
        orders = self.get_data_structure(groups)

        for res in self:
            orders['total']['count'] += 1
            orders['total']['amount_total'] += round(res.amount_total, 2)
            orders['total']['amount_total'] = round(orders['total']['amount_total'], 2)
            orders['total']['order_ids'].append(res.id)
            for g in groups:
                attr = False
                if g == 'month':
                    attr = int(datetime.datetime.strptime(res.date_order, '%Y-%m-%d %H:%M:%S').strftime('%m'))

                if g == 'day':
                    attr = datetime.datetime.strptime(res.date_order, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    attr = datetime.datetime.strptime(attr, '%Y-%m-%d')

                if g == 'is_b2b':
                    attr = res.is_b2b

                if g == 'payment_method_id':
                    attr = res.payment_method_id.name

                if g == 'state':
                    attr = res.state
                if attr:
                    orders[g][attr]['count'] += 1
                    orders[g][attr]['amount_total'] += round(res.amount_total, 2)
                    orders[g][attr]['amount_total'] = round(orders[g][attr]['amount_total'], 2)
                    orders[g][attr]['order_ids'].append(res.id)

        if important_groups:
            for o in orders:
                if o != 'total':
                    for i in orders[o]:
                        if 'order_ids' in orders[o][i]:
                            record = self.search([('id', 'in', orders[o][i]['order_ids'])])
                            orders[o][i]['subdivision'] = record.get_stats(important_groups)

        return orders

    @api.model
    def _generate_data_structure(self, groups, states=None, date_start=None, date_finish=None, payment_method_id=None):
        # crea la struttura dati che serve a raccogliere le statistiche degli ordini
        # groups è una lista di valori per cui raggruppare
        # ['state', 'payment_method_id', 'is_b2b', 'month', 'day']
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
                'order_ids': []
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
        if 'payment_method_id' in groups and payment_method_id is None:
            raise Warning("payment_method_id deve essere inizializzato se 'payment_method_id' è presente in groups")

        for g in groups:
            orders[g] = {}
            if g == 'state':
                for s in states:
                    orders[g][s] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'order_ids': []
                    }
            if g == 'payment_method_id':
                for j in payment_method_id:
                    orders[g][j] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'order_ids': []
                    }
            if g == 'is_b2b':
                orders[g][True] = {
                    'count': 0,
                    'amount_total': 0,
                    'margin': 0,
                    'order_ids': []
                }
                orders[g][False] = {
                    'count': 0,
                    'amount_total': 0,
                    'margin': 0,
                    'order_ids': []
                }
            if g == 'month':
                start = int(datetime.datetime.strptime(date_start, '%Y-%m-%d').strftime('%m'))
                finish = int(datetime.datetime.strptime(date_finish, '%Y-%m-%d').strftime('%m'))
                while start <= finish:
                    orders[g][start] = {
                        'count': 0,
                        'amount_total': 0,
                        'margin': 0,
                        'order_ids': []
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
                        'order_ids': []
                    }
                    start = start + datetime.timedelta(days=1)

        return orders

    @api.multi
    def get_margin(self):
        for order in self:
            if order.picking_ids and order.state not in ['cancel', 'pending', 'draft']:
                return order.picking_ids.get_margin()
            else:
                # qua non posso calcolare un margine preciso, decidere come calcolarlo
                return False
