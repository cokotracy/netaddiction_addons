# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime,date,timedelta
import collections
import io
import csv

class Suppliers(models.Model):
    _inherit = "res.partner"

    export_last_monday = fields.Binary(string="Export ultimo lunedì")

    @api.one 
    def generate_sale_products(self):
        """
        Questa funzione genere il file csv del venduto del lunedì
        da inviare ai fornitori e lo piazza dentro il campo export_monday
        """
        if self.supplier and len(self.parent_id) == 0:
            #è un fornitore padre
            #qua prendo i prodotti venduti nelle ultime 12 settimane
            products = self.get_sale_products_from_12_week()

            today = datetime.now()
            output = io.BytesIO()
            writer = csv.writer(output)
            csvdata = ['SKU','BARCODE','SUPPLIER CODE','PREN','TITOLO','IN VENDITA DAL','PREZZO','W1','W2','W3','W4','W5','W6','W7','W8','W9','W10','W11','W12','TOT','TOTALE STORICO','DA INIZIO ANNO','QTA MAGAZZINO','QTA ORDINATA']
            writer.writerow(csvdata)

            for pid in products:
                csvdata = [pid.id,pid.barcode,'','',pid.display_name,'',pid.final_price,'',]
                for week in range(0,12):
                    w = today - timedelta(weeks=week)
                    iso_week = w.isocalendar()[1]
                    this_week = "%s-W%s" % (w.year,iso_week)
                    sunday = datetime.strptime(this_week + '-0', "%Y-W%W-%w")
                    if sunday in products[pid].keys():
                        csvdata.append(products[pid][sunday])
                    else:
                    	csvdata.append(0)

                writer.writerow(csvdata)


            print output.getvalue()




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

