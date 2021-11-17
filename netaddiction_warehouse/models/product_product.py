import pytz

from calendar import monthrange
from datetime import datetime, date, timedelta
from math import ceil

from odoo import api, fields, models

from ..tools.lib_holidays import is_holiday
from ..tools.nawh_error import NAWHError


class Product(models.Model):
    _inherit = 'product.product'

    days_available = fields.Integer(
        compute="_get_days_available",
        help="Calcola tra quanto potrebbe essere disponibile, se zero è"
             " disponibile immediatamente",
        string="Disponibile in magazzino tra (in giorni)",
    )

    days_shipping = fields.Integer(
        compute="_get_days_shipping",
        string="Consegnato in (in giorni)",
    )

    product_wh_location_line_ids = fields.One2many(
        comodel_name='netaddiction.wh.locations.line',
        inverse_name='product_id',
        string='Allocazioni'
    )

    product_total_inventory = fields.Float(
        string="Valore Totale",
        compute='compute_product_total_inventory'
    )

    def compute_product_total_inventory(self):
        for product in self:
            total_inventory = product.med_inventory_value \
                * product.qty_available
            # TODO if some suppliers exists how change this total_inventory
            #  value like old javascript functionalities?
            # https://github.com/openforceit/netaddiction_addons/blob/9.0/netaddiction_warehouse/static/src/js/inventory_reports.js#L343
            product.product_total_inventory = total_inventory

    def button_activate_product(self):
        """
        Button action copied from old javascript widget that set sale_ok
        status
        """
        self.sale_ok = True

    def button_deactivate_product(self):
        """
        Button action copied from old javascript widget that set sale_ok
        status
        """
        self.sale_ok = False

    @api.model
    def problematic_product(self):
        results = self.search(
            [('qty_available', '<=', 0),
             ('seller_ids.avail_qty', '>', 0),
             ('sale_ok', '=', True),
             '|',
             ('out_date', '<=', date.today()),
             ('out_date', '=', False)]
        )
        alls = self.search(
            [('qty_available', '<=', 0),
             ('sale_ok', '=', True),
             '|',
             ('out_date', '<=', date.today()),
             ('out_date', '=', False)]
        )
        return (alls - results).ids

    def open_product_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name,
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    def do_action_quantity(self):
        """
        funzione che spegne o mette esaurito il prodotto in base alla
        quantità disponibie e quantità limite
        """
        self.ensure_one()
        qty_limit = self.qty_limit
        action = self.limit_action
        # a questo punto faccio le operazioni sullo spegnimento
        if self.qty_available_now <= qty_limit:
            # i sudo ci sono per il customer care
            if action == 'no_purchasable':
                self.sudo().sale_ok = False
                if qty_limit == 0:
                    self.sudo().qty_single_order = 0
                    self.sudo().limit_action = 'nothing'
            if action == 'deactive':
                self.sudo().sale_ok = False
                self.sudo().visible = False
                if qty_limit == 0:
                    self.sudo().qty_single_order = 0
                    self.sudo().limit_action = 'nothing'

    def _get_days_available(self):
        for prod in self:
            prod.days_available = prod.calculate_days_available(
                prod.qty_available_now
            )

    def _get_days_shipping(self):
        """
        dati i giorni disponibili ti dice quando verrà consegnato a casa
        della gente
        """
        default_shipping_days = int(
            self.env['ir.config_parameter'].sudo().get_param('shipping_days')
            or 1
        )
        for prod in self:
            shipping = prod.days_available
            prod.days_shipping = int(prod.calculate_days_shipping(
                shipping, default_shipping_days)
            )

    def calculate_days_shipping(self, shipping, shipping_days):
        """
        calcola la possibile data di consegna a partire da
        shipping = data di processing ordine (days_available) o
            ritorna da calculate_days_available
        shipping_days = tempo di consegna del corriere
        """
        self.ensure_one()
        config_ha = self.env['ir.config_parameter'].sudo() \
            .get_param('hour_available') or '16:00'
        hour_available = datetime.strptime(config_ha, '%H:%M').time()

        config_hna = self.env['ir.config_parameter'].sudo() \
            .get_param('hour_not_available') or '14:00'
        hour_not_available = datetime.strptime(config_hna, '%H:%M').time()

        now = datetime.now(tz=pytz.timezone(self.env.user.tz or 'UTC'))
        now_date = now.date()
        now_time = now.time()

        # per prima cosa controllo se sono dopo hour_available
        # aggiungo un giorno di processing
        if shipping == 0 and now_time > hour_available:
            shipping += 1
        # se invece non ce l'ho disponibile in magazzino controllo se sono dopo
        # hour_not_available nel caso dovessi ordinarlo dal fornitore aggiungo
        # un giorno di processing

        #calcolo il giorno in cui processo il pacco
        day = now_date + timedelta(days=shipping)

        #questo è il giorno in cui dovrei processare l'ordine
        while is_holiday(day):
            day += timedelta(days=1)

        #se il giorno di consegna è festa allora aggiungo
        day += timedelta(days=int(shipping_days))

        while is_holiday(day):
            day += timedelta(days=1)

        diff = day - now_date

        diffdays = diff.days - shipping

        shipping += abs(diffdays)

        return shipping

    def calculate_days_available(self, qty):
        """funzione di appoggio che calcola la disponibilità del prodotto in
        base ad una ipotetica quantità che gli viene passata, ad esempio se
        vuoi comprare 2 qty di un prodotto a disponibilità 1 ti dice
        eventualmente la seconda quantità quando potrebbe essere consegnata

        QUESTA FUNZIONE RITORNA SOLO IL TEMPO DI DISPONIBILITA NEL NOSTRO
        MAGAZZINO
        (es: se domenica ritorna sempre zero)
        """
        self.ensure_one()

        if qty > 0:
            # diamo per scontato che qua ho quantità in magazzino
            return 0

        config_hna = self.env['ir.config_parameter'].sudo() \
            .get_param('hour_not_available') or '14:00'
        hour_not_available = datetime.strptime(config_hna, '%H:%M').time()

        now = datetime.now(tz=pytz.timezone(self.env.user.tz or 'UTC'))
        now_date = now.date()
        now_time = now.time()

        # per prima cosa controllo la data di uscita
        if self.out_date and self.out_date > now_date:
            if self.out_date_approx_type not in (
                'month', 'quarter', 'four', 'year'
            ):
                # se mancano meno di 2 giorni all'uscita do per scontato che
                # ce l'abbiamo in magazzino
                # (molto probabile che lo abbiamo già caricato quindi questo
                # pezzo potrebbe essere superfluo)
                delay = (self.out_date - now_date).days
                if delay <= 2:
                    return 0

                # qui tolgo 1 perchè per default spediamo in un giorno
                # in teoria dovrei mettere il tempo di consegna generico
                # ma avendo più di un corriere è una sega
                return delay - 1

            year = self.out_date.year
            if self.out_date_approx_type == 'month':
                month = self.out_date.month
            elif self.out_date_approx_type == 'quarter':
                month = ceil(self.out_date.month / 3) * 3
            elif self.out_date_approx_type == 'four':
                month = ceil(self.out_date.month / 4) * 4
            else:
                month = 12

            _, day = monthrange(year, month)
            period_date = date(year, month, day)
            delay = (period_date - now_date).days
            return delay

        if self.available_date and self.available_date > now_date:
            return (self.available_date - now_date).days

        # controllo i fornitori che hanno la qty > 0
        # prendo il fornitore a priorità più alta (se ce ne sono due con la
        # stessa priorità prendo quello a prezzo più basso)
        supplier = self.env['res.partner']
        backup_supplier = self.env['res.partner']
        priority = 0
        backup_priority = 0
        price = 9999
        backup_price = 99999
        delay = 0

        # calcolo quando farò l'ordine
        retarded = 0
        if now_time > hour_not_available and not is_holiday(now_date):
            retarded += 1

        this_moment = now_date + timedelta(days=retarded)
        while is_holiday(this_moment):
            this_moment += timedelta(days=1)
            retarded += 1

        # qua uso sudo per dare la possibilità di leggere questo campo
        # anche a chi non ha i permessi sui fornitori
        for sup in self.sudo().seller_ids:
            # prendo solo fornitori attivi e con qtà disponibile positiva
            if sup.name.active and sup.avail_qty > 0:
                # Se la priorità è più alta, prendo il fornitore e aggiorno
                # i parametri
                if int(sup.name.supplier_priority) > int(priority):
                    supplier = sup
                    priority = sup.name.supplier_priority
                    price = sup.price
                    delay = sup.delay
                # Se la priorità è la stessa ma il prezzo è inferiore, prendo
                # il fornitore e aggiorno i parametri
                elif int(sup.name.supplier_priority) == int(priority) \
                        and sup.price < price:
                    supplier = sup
                    priority = sup.name.supplier_priority
                    price = sup.price
                    delay = sup.delay
                # Se priorità e prezzo sono gli stessa ma il tempo di consegna
                # è inferiore, prendo il fornitore e aggiorno i parametri
                elif int(sup.name.supplier_priority) == int(priority) \
                        and sup.price == price \
                        and sup.delay < delay:
                    supplier = sup
                    priority = sup.name.supplier_priority
                    price = sup.price
                    delay = sup.delay

                # eventualmente ci fosse casino con il delay mi salvo sempre un
                # fornitore di backup a priorità più alta
                if int(sup.name.supplier_priority) >= int(backup_priority) \
                        and sup.price <= backup_price:
                    backup_supplier = sup
                    backup_priority = sup.name.supplier_priority
                    backup_price = sup.price

        supplier = supplier or backup_supplier

        if not supplier:
            # se proprio non ho trovato niente
            return 730

        day = now_date + timedelta(days=supplier.delay + retarded)
        while is_holiday(day):
            day += timedelta(days=1)
        return (day - now_date).days

    def _get_product_from_barcode(self, barcode):
        if isinstance(barcode, (tuple, list, set)):
            domain = [('barcode', 'in', list(barcode))]
        else:
            domain = [('barcode', '=', barcode)]

        # Return whatever is found or an error instead
        return self.search(domain) or NAWHError("Barcode Inesistente")

    def get_allocation(self):
        alloc_obj = self.env['netaddiction.wh.locations.line']
        domain = [('product_id', 'in', self.ids)]
        order = 'wh_location_id'
        err_msg = "Prodotto non presente nel magazzino"

        # Return whatever is found or an error instead
        return alloc_obj.search(domain, order=order) or NAWHError(err_msg)

    ##########################
    # INVENTORY APP FUNCTION #
    # ritorna un dict simile #
    # ad un json per il web  #
    ##########################

    @api.model
    def check_product(self, barcode):
        product = self._get_product_from_barcode(barcode)
        if isinstance(product, NAWHError):
            return {'result': 0, 'error': product.msg}
        # Return the first product ID
        return {'result': 1, 'product_id': product.ids[:1]}

    @api.model
    def get_json_allocation(self, barcode):
        """
        ritorna un json con i dati per la ricerca per prodotto
        """
        product = self._get_product_from_barcode(barcode)
        if isinstance(product, NAWHError):
            return {'result': 0, 'error': product.msg}

        allocations = product.get_allocation()
        if isinstance(allocations, NAWHError):
            return {'result': 0, 'error': allocations.msg}

        return {
            'result': 1,
            'product': product.display_name,
            'barcode': product.barcode,
            'product_id': product.id,
            'allocations': [
                {'shelf': a.wh_location_id.name,
                 'qty': a.qty,
                 'line_id': a.id}
                for a in allocations
            ],
            'qty_available_now': product.qty_available_now
        }

    ##############################
    # END INVENTORY APP FUNCTION #
    ##############################

    ###########
    # PICK UP #
    ###########

    def get_shelf_to_pick(self, qty):
        """
        Passando la quantità da pickuppare (qty), la funzione restituisce
        il/i ripiano/i da cui scaricare il prodotto in totale autonomia

        ritorna un dict {'location': 'quantità da scaricare'}
        """
        self.ensure_one()
        shelf = {}
        for alloc in self.product_wh_location_line_ids:
            if qty > 0:
                if qty <= alloc.qty:
                    shelf[alloc.wh_location_id] = qty
                    qty = 0
                else:
                    shelf[alloc.wh_location_id] = alloc.qty
                    qty -= alloc.qty
        return shelf

    def order_shelf(self):
        # ordina i ripiani del prodotto
        self.ensure_one()
        v = {}
        pre = []
        middle = []
        for loc in self.product_wh_location_line_ids:
            sp = loc.wh_location_id.name.split('/')
            pre.append(sp[0])
            middle.append(int(sp[1]))
        pre = list(set(pre))
        middle = list(set(middle))
        pre.sort()
        middle.sort()
        for loc in self.product_wh_location_line_ids:
            sp = loc.wh_location_id.name.split('/')
            pind = pre.index(sp[0])
            mind = middle.index(int(sp[1]))
            if pind not in list(v.keys()):
                v[pind] = {}
            if mind not in list(v[pind].keys()):
                v[pind][mind] = [loc]
            else:
                v[pind][mind].append(loc)

        result = []
        for i in v:
            for t in v[i]:
                result += v[i][t]
        return result

    ################################
    # END PICK UP / RESO FORNITORE #
    ################################
    # TODO the action client reso fornitore has been removed
    # @api.model
    # def get_product_from_supplier(self, supplier_id):
    #     # TODO maybe manage this records with a search_read and compute inventory_value from javascript
    #     # Get all the supplier info for selected supplier
    #     seller_supplierinfo = self.env['product.supplierinfo'].search([
    #         ('name', '=', int(supplier_id))
    #     ])
    #     # Get all the products that uses supplier info pricelists
    #     seller_products = self.search([
    #         ('company_id', '=', self.env.user.company_id.id),
    #         ('seller_ids', 'in', seller_supplierinfo.ids),
    #         ('qty_available', '>', 0),
    #     ])
    #     product_data = {}
    #     for product in seller_products:
    #         qty = product.qty_available
    #         inventory_value = qty * product.standard_price
    #         single_inventory = product.standard_price
    #         if product.id in product_data:
    #             product_data[product.id]['qty'] = qty
    #             product_data[product.id]['inventory_value'] = inventory_value
    #             product_data[product.id]['single_inventory'] = single_inventory
    #         else:
    #             product_data[product.id] = {
    #                 'id': product.id,
    #                 'name': product.display_name,
    #                 'qty': qty,
    #                 'inventory_value': inventory_value,
    #                 'single_inventory': single_inventory
    #             }
    #     return product_data

    # @api.model
    # def get_scraped_product_from_supplier(self, supplier_id):
    #     # TODO maybe manage this records with a search_read and compute inventory_value from javascript
    #     # TODO How get scraped products from supplier?
    #     # Get all the supplier info for selected supplier
    #     seller_supplierinfo = self.env['product.supplierinfo'].search([
    #         ('name', '=', int(supplier_id))
    #     ])
    #     # Get all the products that uses supplier info pricelists
    #     seller_products = self.search([
    #         ('company_id', '=', self.env.user.company_id.id),
    #         ('seller_ids', 'in', seller_supplierinfo.ids),
    #         ('qty_available', '>', 0),
    #     ])
    #     product_data = {}
    #     for product in seller_products:
    #         qty = product.qty_available
    #         inventory_value = qty * product.standard_price
    #         single_inventory = product.standard_price
    #         if product.id in product_data:
    #             product_data[product.id]['qty'] = qty
    #             product_data[product.id]['inventory_value'] = inventory_value
    #             product_data[product.id]['single_inventory'] = single_inventory
    #         else:
    #             product_data[product.id] = {
    #                 'id': product.id,
    #                 'name': product.display_name,
    #                 'qty': qty,
    #                 'inventory_value': inventory_value,
    #                 'single_inventory': single_inventory
    #             }
    #     return product_data

    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        print('-------------------------------------------------')
        print('self, args, offset, limit, order, count, access_rights_uid')
        print(self, args, offset, limit, order, count, access_rights_uid)
        print('-------------------------------------------------')
        # import pdb;pdb.set_trace()
        return super()._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
