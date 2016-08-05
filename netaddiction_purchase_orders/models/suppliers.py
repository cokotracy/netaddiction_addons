# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime,date,timedelta
import collections
import io
import csv
import base64

class Suppliers(models.Model):
    _inherit = "res.partner"

    send_report = fields.Boolean(string="Il fornitore riceve i report del lunedì", default = False)

    send_contact_report = fields.Boolean(string="Il contatto riceve i report del lunedì", default = False)
    send_contact_purchase_orders = fields.Boolean(string="Il contatto riceve gli ordini di acquisto", default = False)
    send_contact_refund = fields.Boolean(string="Il contatto riceve i resi", default = False)

    @api.one
    def generate_slow_moving(self):
        """
        genera il file dello slow moving 
        i prodotti in magazzino di questo fornitore che non sono stati venduti nelle ultime 12 settimane
        """

        #prendo i prodotti che ho in magazzino associati a questo fornitore
        self.ensure_one()
        today = datetime.now()
        twelve_week = timedelta(weeks=12)
        date_from = today-twelve_week
        products_12 = []
        products_slow = []
        location_id = self.env['stock.location'].search([('usage','=','customer')]).id
        
        products_all = self.get_products_sale_all_time()
        products_this_year = self.get_products_sale_this_year()

        #i prodotti movimentati nelle ultime 12 settimane.
        order_lines = self.env['sale.order.line'].search([('order_id.date_order','>=',date_from.strftime('%Y-%m-%d %H:%M:%S')),('product_id.seller_ids.name','=',self.id),
            ('company_id','=',self.env.user.company_id.id)])

        wh = self.env['stock.location'].search([('company_id','=',self.env.user.company_id.id),('active','=',True),
            ('usage','=','internal'),('scrap_location','=',False)])

        for quant in order_lines:
            if quant.product_id not in products_12:
                products_12.append(quant.product_id)

        #i prodotti in magazzino
        quants = self.env['stock.quant'].search([('location_id','=',wh.id),
            ('history_ids.picking_id.partner_id','=',self.id),('company_id','=',self.env.user.company_id.id)])        

        for quant in quants:
            if quant.product_id not in products_12:
                products_slow.append(quant.product_id)

        # a questo punto, tecnicamente in products_slow ho una lista di prodotti di questo fornitore
        # che non vendo da un botto di tempo

        output = io.BytesIO()
        writer = csv.writer(output)
        csvdata = [u'SKU',u'BARCODE',u'SUPPLIER CODE',u'TITOLO',u'PREZZO',u'TOT12',u'TOTALE STORICO',u'DA INIZIO ANNO',u'QTA MAGAZZINO']
        writer.writerow(csvdata)

        for product in products_slow:
            #qua prendo il supplier code del prodotto
            sup_code = ''
            for sell in product.seller_ids:
                if sell.name.id == self.id:
                    sup_code = sell.product_code

            #prendo il prezzo TODO : controllare dopo
            price = product.final_price
            if product.offer_price > 0:
                price = product.offer_price
            elif product.special_price > 0:
                price = product.special_price

            csvdata = [product.id,product.barcode,sup_code,product.display_name,price,0]

            if product.id in products_all.keys():
                csvdata.append(int(products_all[product.id]))
            else:
                csvdata.append(0)

            if product.id in products_this_year.keys():
                csvdata.append(int(products_this_year[product.id]))
            else:
                csvdata.append(0)

            csvdata.append(int(product.qty_available))

            writer.writerow(unicode(csvdata))

        name = 'slow_moving_multiplayer_com_' + self.name + '_' + str(date.today()) + '.csv'
        
        attachment = {
               'name': name,
               'datas_fname': name,
               'datas': base64.b64encode(output.getvalue()).decode(),
           }

        attachment_id = self.env['ir.attachment'].create(attachment)

        output.close()

        return attachment_id

    @api.one 
    def generate_monday_report(self):
        """
        Questa funzione genere il file csv del venduto del lunedì
        da inviare ai fornitori e lo piazza dentro il campo export_monday
        """
        if self.supplier and len(self.parent_id) == 0:
            #è un fornitore padre
            #qua prendo i prodotti venduti nelle ultime 12 settimane
            products = self.get_sale_products_from_12_week()
            products_all = self.get_products_sale_all_time()
            products_this_year = self.get_products_sale_this_year()

            products_purchase = self.get_purchase_products()

            today = datetime.now()
            output = io.BytesIO()
            writer = csv.writer(output)
            csvdata = [u'SKU',u'BARCODE',u'SUPPLIER CODE',u'PREN',u'TITOLO',u'PREZZO',u'W1',u'W2',u'W3',u'W4',u'W5',u'W6',u'W7',u'W8',u'W9',u'W10',u'W11',u'W12',u'TOT12',u'TOTALE STORICO',u'DA INIZIO ANNO',u'QTA MAGAZZINO',u'QTA ORDINATA']
            writer.writerow(csvdata)

            for pid in products:
                #qua prendo il supplier code del prodotto
                sup_code = ''
                for sell in pid.seller_ids:
                    if sell.name.id == self.id:
                        sup_code = sell.product_code
                #scopro se prenotazione
                pren = ''
                product_date = ''
                if pid.out_date:
                    product_date = datetime.strptime(pid.out_date, "%Y-%m-%d")
                if product_date:
                    if datetime.now() < product_date:
                        pren = 'P'
                #prendo il prezzo TODO : controllare dopo
                price = pid.final_price
                if pid.offer_price > 0:
                    price = pid.offer_price
                elif pid.special_price > 0:
                    price = pid.special_price

                csvdata = [pid.id,pid.barcode,sup_code,pren,pid.display_name,price,]
                tot12 = 0
                for week in range(0,12):
                    w = today - timedelta(weeks=week)
                    iso_week = w.isocalendar()[1]
                    this_week = "%s-W%s" % (w.year,iso_week)
                    sunday = datetime.strptime(this_week + '-0', "%Y-W%W-%w")
                    if sunday in products[pid].keys():
                        csvdata.append(int(products[pid][sunday]))
                        tot12 += int(products[pid][sunday])
                    else:
                        csvdata.append(0)
                
                csvdata.append(tot12)

                if pid.id in products_all.keys():
                    csvdata.append(int(products_all[pid.id]))
                else:
                    csvdata.append(0)

                if pid.id in products_this_year.keys():
                    csvdata.append(int(products_this_year[pid.id]))
                else:
                    csvdata.append(0)
                
                csvdata.append(int(pid.qty_available))

                if pid.id in products_purchase.keys():
                    csvdata.append(int(products_purchase[pid.id]))
                else:
                    csvdata.append(0)

                line = []
                for c in csvdata:
                    line.append(unicode(c))
                writer.writerow(line)

        name = 'export_multiplayer_com_' + self.name + '_' + str(date.today()) + '.csv'
        
        attachment = {
               'name': name,
               'datas_fname': name,
               'datas': base64.b64encode(output.getvalue()).decode(),
           }

        attachment_id = self.env['ir.attachment'].create(attachment)

        output.close()

        return attachment_id

    @api.multi
    def get_sale_products_from_12_week(self):
        """
        restituisce un dict 
        che contiene prodotto => quantità per data 
        dove la data è la domenica finale della settimana interessata
        """
        #mi prendo il location_id corretto, quello dei clienti
        # TODO : piazzo un todo se qualcuno dovesse creare un domani una cazzo di location nuova per un altro sito senza chiedere il permesso
        self.ensure_one()
        location_id = self.env['stock.location'].search([('usage','=','customer')]).id

        weeks_subdivision = {}

        today = datetime.now()
        twelve_week = timedelta(weeks=12)
        date_from = today-twelve_week
        #suddivido le dodici settimane
        this_number_week = today.isocalendar()[1]
        this_week = "%s-W%s" % (today.year,this_number_week)
        #dovrebbe essere la domenica di questa settimana
        this_sunday = datetime.strptime(this_week + '-0', "%Y-W%W-%w")
        weeks_subdivision[this_sunday] = 0
        #da qui vado indietro di 12 volte (le 12 settimane)
        for week in range(1,12):
            w = today - timedelta(weeks=week)
            iso_week = w.isocalendar()[1]
            this_week = "%s-W%s" % (w.year,iso_week)
            sunday = datetime.strptime(this_week + '-0', "%Y-W%W-%w")
            weeks_subdivision[sunday] = 0

        #i prodotti movimentati nelle ultime 12 settimane.
        quants = self.env['stock.quant'].search([('in_date','>=',date_from.strftime('%Y-%m-%d %H:%M:%S')),('location_id','=',location_id),
            ('history_ids.picking_id.partner_id','=',self.id),('company_id','=',self.env.user.company_id.id)])
        #i prodotti che non sono stati movimentati ma sono in prenotazione.
        order_lines = self.env['sale.order.line'].search([('order_id.date_order','>=',date_from.strftime('%Y-%m-%d %H:%M:%S')),('product_id.seller_ids.name','=',self.id),
            ('product_id.out_date','>=',today.strftime('%Y-%m-%d %H:%M:%S')),('company_id','=',self.env.user.company_id.id)])

        products = {}

        for line in order_lines:
            if line.product_id not in products.keys():
                products[line.product_id] = {}
            for sunday in sorted(weeks_subdivision.keys(),reverse=True):
                if datetime.strptime(line.order_id.date_order,'%Y-%m-%d %H:%M:%S') >= sunday - timedelta(6):
                    if sunday not in products[line.product_id].keys():
                        products[line.product_id][sunday] = 0

                    products[line.product_id][sunday] += line.product_qty
                    break

        for quant in quants:
            if quant.product_id not in products.keys():
                products[quant.product_id] = {}
            for sunday in sorted(weeks_subdivision.keys(),reverse=True):
                if datetime.strptime(quant.in_date,'%Y-%m-%d %H:%M:%S') >= sunday - timedelta(6):
                    if sunday not in products[quant.product_id].keys():
                        products[quant.product_id][sunday] = 0

                    products[quant.product_id][sunday] += quant.qty
                    break

        return products

    @api.multi
    def get_products_sale_all_time(self):
        """
        prendo i prodotti di questo fornitore venduti nei secoli dei secoli
        """
        self.ensure_one()
        today = datetime.now()
        location_id = self.env['stock.location'].search([('usage','=','customer')]).id

        #i prodotti movimentati nelle ultime 12 settimane.
        quants = self.env['stock.quant'].read_group(domain = [('location_id','=',location_id),('product_id.active','=',True),
            ('history_ids.picking_id.partner_id','=',self.id),('company_id','=',self.env.user.company_id.id)], fields = ['product_id' , 'qty'], groupby = ['product_id'])


        #i prodotti che non sono stati movimentati ma sono in prenotazione.
        order_lines = self.env['sale.order.line'].read_group(domain = [('product_id.seller_ids.name','=',self.id),('product_id.active','=',True),
            ('product_id.out_date','>=',today.strftime('%Y-%m-%d %H:%M:%S')),('company_id','=',self.env.user.company_id.id)], fields = ['product_id' , 'product_uom_qty'], groupby = ['product_id'])

        products = {}

        for quant in quants:
            if quant['product_id'][0] not in products.keys():
                products[quant['product_id'][0]] = 0

            products[quant['product_id'][0]] += quant['qty']

        for line in order_lines:
            if line['product_id'][0] not in products.keys():
                products[line['product_id'][0]] = 0

            products[line['product_id'][0]] += line['product_uom_qty']

        return products


    @api.multi
    def get_products_sale_this_year(self):
        """
        prendo i prodotti venduti da inizio anno
        """
        self.ensure_one()
        today = datetime.now()
        location_id = self.env['stock.location'].search([('usage','=','customer')]).id
        date_from = date(date.today().year, 1, 1)


        #i prodotti movimentati nelle ultime 12 settimane.
        quants = self.env['stock.quant'].read_group(domain = [('in_date','>=',date_from.strftime('%Y-%m-%d %H:%M:%S')),('location_id','=',location_id),('product_id.active','=',True),
            ('history_ids.picking_id.partner_id','=',self.id),('company_id','=',self.env.user.company_id.id)], fields = ['product_id' , 'qty'], groupby = ['product_id'])


        #i prodotti che non sono stati movimentati ma sono in prenotazione.
        order_lines = self.env['sale.order.line'].read_group(domain = [('product_id.seller_ids.name','=',self.id),('product_id.active','=',True),
            ('order_id.date_order','>=',date_from.strftime('%Y-%m-%d %H:%M:%S')),
            ('product_id.out_date','>=',today.strftime('%Y-%m-%d %H:%M:%S')),('company_id','=',self.env.user.company_id.id)], fields = ['product_id' , 'product_uom_qty'], groupby = ['product_id'])

        products = {}

        for quant in quants:
            if quant['product_id'][0] not in products.keys():
                products[quant['product_id'][0]] = 0

            products[quant['product_id'][0]] += quant['qty']

        for line in order_lines:
            if line['product_id'][0] not in products.keys():
                products[line['product_id'][0]] = 0

            products[line['product_id'][0]] += line['product_uom_qty']

        return products

    @api.multi
    def get_purchase_products(self):
        self.ensure_one()

        purchase_lines = self.env['purchase.order.line'].read_group(domain = [('order_id.state','=','purchase'),('order_id.partner_id','=',self.id)], fields = ['product_id','product_qty'], groupby = ['product_id'])

        products = {}

        for line in purchase_lines:
            if line['product_id'][0] not in products.keys():
                products[line['product_id'][0]] = 0

            products[line['product_id'][0]] += line['product_qty']

        return products