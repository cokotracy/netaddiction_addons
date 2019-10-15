# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
from error import Error
import lib_holidays
from calendar import monthrange
import pytz

class Products(models.Model):
    _inherit = 'product.product'

    days_available = fields.Integer(string="Disponibile in magazzino Tra (in giorni)",help="Calcola tra quanto potrebbe essere disponibile, se zero è disponibile immediatamente",
            compute="_get_days_available")

    days_shipping = fields.Integer(string="Consegnato in (in giorni)", compute = "_get_days_shipping")

    @api.model
    def problematic_product(self):
        results = self.search([('qty_available', '<=', 0), ('seller_ids.avail_qty', '>', 0), ('sale_ok', '=', True), '|', ('out_date', '<=', datetime.date.today()), ('out_date', '=', False)])
        alls = self.search([('qty_available', '<=', 0), ('sale_ok', '=', True), '|', ('out_date', '<=', datetime.date.today()), ('out_date', '=', False)])
        res = alls - results
        return res.mapped('id')

    @api.multi
    def open_product_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': '%s' % self.display_name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    @api.multi
    def do_action_quantity(self):
        """
        funzione che spegne o mette esaurito il prodotto in base alla quantità disponibie e quantità limite
        """
        # i sudo ci sono per il customer care
        qty_limit = self.qty_limit
        qty_single = self.qty_single_order
        action = self.limit_action
        # a questo punto faccio le operazioni sullo spegnimento
        if self.qty_available_now <= qty_limit:
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

    @api.one 
    def _get_days_available(self):
        today = datetime.date.today()
        self.days_available = self.calculate_days_available(self.qty_available_now)

    @api.one 
    def _get_days_shipping(self):
        """
        dati i giorni disponibili ti dice quando verrà consegnato a casa della gente
        """
        shipping = self.days_available
        sd = 1
        res = self.env["ir.values"].search([("name","=","shipping_days")])
        for r in res:
            sd = r.value

        shipping_days = sd

        self.days_shipping = int(self.calculate_days_shipping(shipping,shipping_days))

    @api.multi 
    def calculate_days_shipping(self,shipping,shipping_days):
        """
        calcola la possibile data di consegna a partire da 
        shipping = data di proccessing ordine (days_available) o ritorna da calculate_days_available
        shipping_days = tempo di consegna del corriere
        """

        holiday = lib_holidays.LibHolidays()
        res = self.env["ir.values"].search([("name", "=", "hour_available")])
        ha = '16:00'
        for r in res:
            ha = r.value
        hour_available = datetime.datetime.time(datetime.datetime.strptime(ha, '%H:%M'))

        hna = '14:00'
        res = self.env["ir.values"].search([("name", "=", "hour_not_available")])
        for r in res:
            hna = r.value
        hour_not_available = datetime.datetime.time(datetime.datetime.strptime(hna, '%H:%M'))

        time_now = datetime.datetime.time(datetime.datetime.now(tz=pytz.timezone(self.env.user.tz)))
        today = datetime.datetime.now(tz=pytz.timezone(self.env.user.tz)).date()

        # per prima cosa controllo se sono dopo hour_available
        # aggiungo un giorno di processing
        if shipping == 0 and time_now > hour_available:
            shipping += 1
        # se invece non ce l'ho disponibile in magazzino controllo se sono dopo hour_not_available
        # nel caso dovessi ordinarlo dal fornitore aggiungo un giorno di processing

        #calcolo il giorno in cui processo il pacco
        day = today + datetime.timedelta(days=shipping)
        
        #questo è il giorno in cui dovrei processare l'ordine
        while holiday.is_holiday(day):
            day += datetime.timedelta(days=1)

        #se il giorno di consegna è festa allora aggiungo
        day += datetime.timedelta(days=int(shipping_days))

        while holiday.is_holiday(day):
            day += datetime.timedelta(days=1)

        diff = day - today

        diffdays = diff.days - shipping

        shipping += abs(diffdays)

        return shipping


    @api.multi
    def calculate_days_available(self,qty):
        """funzione di appoggio che calcola la disponibilità del prodotto in base ad una ipotetica quantità che gli
        viene passata, ad esempio se vuoi comprare 2 qty di un prodotto a disponibilità 1 ti dice eventualmente
        la seconda quantità quando potrebbe essere consegnata

        QUESTA FUNZIONE RITORNA SOLO IL TEMPO DI DISPONIBILITA NEL NOSTRO MAGAZZINO
        (es: se domenica ritorna sempre zero)
        """
        holiday = lib_holidays.LibHolidays()
        today = datetime.date.today()
        res = self.env["ir.values"].search([("name","=","hour_not_available")])

        hna = '14:00'
        for r in res:
            hna = r.value
        hour_not_available = datetime.datetime.time(datetime.datetime.strptime(hna , '%H:%M'))

        time_now = datetime.datetime.time(datetime.datetime.now(tz = pytz.timezone(self.env.user.tz)))
        self.ensure_one()
        if qty>0:
            #diamo per scontato che qua ho quantità in magazzino
            return 0
        else:
            #per prima cosa controllo la data di uscita
            if self.out_date is not False and datetime.datetime.strptime(self.out_date,"%Y-%m-%d").date() > datetime.date.today():
                delay = (datetime.datetime.strptime(self.out_date,"%Y-%m-%d").date() - today).days

                if self.out_date_approx_type == 'month':
                    month = datetime.datetime.strptime(self.out_date,"%Y-%m-%d").month
                    year = datetime.datetime.strptime(self.out_date,"%Y-%m-%d").year
                if self.out_date_approx_type == 'quarter':
                    last_month = {
                        1:3,
                        2:6,
                        3:9,
                        4:12
                    }
                    period = (datetime.datetime.strptime(self.out_date,"%Y-%m-%d").month -1) / 3 +1

                    month = last_month[period]
                    year = datetime.datetime.strptime(self.out_date,"%Y-%m-%d").year
                if self.out_date_approx_type == 'four':
                    last_month = {
                        1:4,
                        2:8,
                        3:9,
                    }
                    period = (datetime.datetime.strptime(self.out_date,"%Y-%m-%d").month -1) / 4 +1

                    month = last_month[period]
                    year = datetime.datetime.strptime(self.out_date,"%Y-%m-%d").year
                if self.out_date_approx_type == 'year':
                    month = 12
                    year = datetime.datetime.strptime(self.out_date,"%Y-%m-%d").year

                if self.out_date_approx_type == 'accurate' or self.out_date_approx_type == 'nothing' or self.out_date_approx_type == False:
                    #se mancano meno di 2 giorni all'uscita do per scontato che ce l'abbiamo in magazzino
                    #(molto probabile che lo abbiamo già caricato quindi questo pezzo potrebbe essere superfluo)
                    if delay <= 2:
                       return 0 

                    #qui tolgo 1 perchè per default spediamo in un giorno
                    #in teoria dovrei mettere il tempo di consegna generico
                    #ma avendo più di un corriere è una sega
                    return delay - 1 

                mrange = monthrange(year, month)
                period_date = datetime.datetime(year,month,mrange[1])
                delay = (period_date.date() - today).days

                return delay
            else:
                if self.available_date is not False and datetime.datetime.strptime(self.available_date,"%Y-%m-%d").date() > datetime.date.today():
                    return (datetime.datetime.strptime(self.available_date,"%Y-%m-%d").date() - today).days
                else:
                    if self.out_date_approx_type == 'nothing':
                        return 730
                    #controllo i fornitori che hanno la qty > 0
                    #prendo il fornitore a priorità più alta (se ce ne sono due con la stessa priorità prendo quello a prezzo più basso)
                    supplier = 0
                    this_priority = 0
                    qty = 0
                    price = 9999
                    delay = 0

                    supplier_best_backup = 0
                    backup_priority = 0
                    backup_price = 99999

                    #calcolo quando farò l'ordine
                    retarded = 0
                    if time_now > hour_not_available and not holiday.is_holiday(datetime.datetime.now()):
                        retarded += 1
                
                    this_moment = datetime.date.today() + datetime.timedelta(days = retarded)
                    while holiday.is_holiday(this_moment):
                        this_moment += datetime.timedelta(days = 1)
                        retarded += 1

                    #qua uso sudo per dare la possibilità di leggere questo campo
                    #anche a chi non ha i permessi sui fornitori
                    for sup in self.sudo().seller_ids:
                        if sup.name.active:
                            if int(sup.name.supplier_priority) > int(this_priority) and int(sup.avail_qty) > 0:
                                supplier = sup
                                this_priority = sup.name.supplier_priority
                                price = sup.price
                                qty = sup.avail_qty
                                delay = sup.delay
                            else:
                                if int(sup.name.supplier_priority) == int(this_priority) and int(sup.avail_qty) > 0:
                                    if sup.price < price:
                                        qty = sup.avail_qty
                                        delay = sup.delay
                                        supplier = sup
                                        this_priority = sup.name.supplier_priority
                                        price = sup.price
                                    elif sup.price == price and sup.delay < delay:
                                        qty = sup.avail_qty
                                        delay = sup.delay
                                        supplier = sup
                                        this_priority = sup.name.supplier_priority
                                        price = sup.price

                            #eventualmente ci fosse casino con il delay mi salvo sempre un 
                            #fornitore di backup a priorità più alta
                            if int(sup.name.supplier_priority) >= int(backup_priority) and sup.price <= backup_price :
                                supplier_best_backup = sup
                                backup_priority = sup.name.supplier_priority
                                backup_price = sup.price

                    if supplier == 0:
                        if supplier_best_backup == 0:
                            #se proprio non ho trovato niente
                            return 730
                        else:
                            day = datetime.date.today() + datetime.timedelta(days = supplier_best_backup.delay) + datetime.timedelta(days = retarded)
                            while holiday.is_holiday(day):
                                day += datetime.timedelta(days = 1)
                            return (day - datetime.date.today()).days 
                    else:
                        day = datetime.date.today() + datetime.timedelta(days = supplier.delay) + datetime.timedelta(days = retarded)
                        while holiday.is_holiday(day):
                            day += datetime.timedelta(days = 1)
                        return (day - datetime.date.today()).days 


    @api.model
    def _get_product_from_barcode(self,barcode):
        if isinstance(barcode, list):
            attr=[('barcode','in',barcode)]
        else:
            attr = [('barcode','=',barcode)]
            
        product = self.search(attr)

        if len(product)==0:
            err = Error()
            err.set_error_msg("Barcode Inesistente")
            return err

        return product

    @api.model
    def get_allocation(self):
        result = self.env['netaddiction.wh.locations.line'].search([('product_id','=',self.id)],order='wh_location_id')
        if len(result)==0:
            err = Error()
            err.set_error_msg("Prodotto non presente nel magazzino")
            return err

        return result

    ########################
    #INVENTORY APP FUNCTION#
    #ritorna un dict simile#
    #ad un json per il web #
    ########################
    @api.model
    def check_product(self,barcode):
        product = self._get_product_from_barcode(barcode)
        if isinstance(product,Error):
            return {'result' : 0, 'error' : product.get_error_msg()}

        return {'result' : 1 , 'product_id' : product.id}


    @api.model
    def get_json_allocation(self,barcode):
        """
        ritorna un json con i dati per la ricerca per porodotto
        """
        product = self._get_product_from_barcode(barcode)  

        if isinstance(product,Error):
            return {'result' : 0, 'error' : product.get_error_msg()}

        results = product.get_allocation()

        if isinstance(results,Error):
            return {'result' : 0, 'error' : results.get_error_msg()}

        allocations = {
            'result' : 1,
            'product' : product.display_name,
            'barcode' : product.barcode,
            'product_id' : product.id,
            'allocations' : [],
            'qty_available_now': product.qty_available_now
        }
        for res in results:
            allocations['allocations'].append({'shelf':res.wh_location_id.name,'qty':res.qty, 'line_id': res.id})

        return allocations

    ############################
    #END INVENTORY APP FUNCTION#
    ############################

    
    #########
    #PICK UP#
    #########
    @api.multi 
    def get_shelf_to_pick(self,qty):
        """
        Passando la quantità da pickuppare (qty), la funzione restituisce il/i ripiano/i 
        da cui scaricare il prodotto in totale autonomia
        ritorna una lista di dict {'location_id','quantità da scaricare'}
        """
        self.ensure_one()
        shelf = {}
        for alloc in self.product_wh_location_line_ids:
            if qty>0:
                if qty <= alloc.qty:
                    shelf[alloc.wh_location_id] = int(qty) 
                    qty = 0
                else:
                    shelf[alloc.wh_location_id] = int(alloc.qty) 
                    qty = int(qty) - int(alloc.qty)

        return shelf

    @api.multi
    def order_shelf(self):
        # ordina i ripiani del prodotto
        self.ensure_one
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
            if pind not in v.keys():
                v[pind] = {}
            if mind not in v[pind].keys():
                v[pind][mind] = [loc]
            else:
                v[pind][mind].append(loc)

        result = []
        for i in v:
            for t in v[i]:
                result += v[i][t]
        return result

class ConfigShippingTime(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'netaddiction.shipping.time'

    hour_available = fields.Char(string="Ora oltre la quale la spedizione non è più immediata ma slitta a domani",default="16:00")
    hour_not_available = fields.Char(string="Ora oltre la quale la spedizione di prodotti non presenti in magazzino slitta di un giorno",default="14:00")

    shipping_days = fields.Integer(string="Giorni di spedizione di default (può essere anche una media)")

    @api.one
    def set_hour_available(self,values):
        self.env['ir.values'].create({'name':'hour_available','value':self.hour_available,'model':'netaddiction.shipping.time'})

    @api.one
    def set_shipping_days(self,values):
        self.env['ir.values'].create({'name':'shipping_days','value':self.shipping_days,'model':'netaddiction.shipping.time'})

    @api.one
    def set_hour_not_available(self,values):
        self.env['ir.values'].create({'name':'hour_not_available','value':self.hour_not_available,'model':'netaddiction.shipping.time'})

    #@api.model
    #def get_default_values(self,fields):
    #    values = self.env['ir.values'].search([('model','=','netaddiction.shipping.time')])
    #    attr = {
    #        'hour_available' : '16:00',
    #        'hour_not_available' : '14:00',
    #        'shipping_days' : 1
    #    }
    #    for v in values:
    #        attr[v.name] = v.value
    #    return attr


