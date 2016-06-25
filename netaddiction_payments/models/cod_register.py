# -*- coding: utf-8 -*-
import csv
import base64
import io
from openerp import models, fields, api
from openerp.exceptions import Warning

BRT = "Numero riferimento spedizione"
SDA = "Riferimenti"
MONEY_BRT = "Euro"
MONEY_SDA = "Importo contrassegno"


def strip_keys(d):
#funzione di utilità che per effettuare lo stip delle chiavi di un dizionario 
    return   {k.strip():strip_keys(v)
             if isinstance(v, dict)
             else v
             for k, v in d.iteritems()}


class CoDRegister(models.TransientModel):
    
    _name = "netaddiction.cod.register"

    csv_file = fields.Binary('File')


    @api.one
    def set_order_cash_on_delivery(self,order_id):
        order = self.env["sale.order"].search([("id","=",order_id)])
        if order:
            if order.state == 'draft':
                order.action_confirm()

            if order.state == 'sale':
                contrassegno = self.env['ir.model.data'].get_object('netaddiction_payments', 'product_contrassegno')
                order.payment_method_id = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal').id
                inv_lst = []
                print "LEN %s" % len(order.picking_ids)
                for line in order.order_line:
                    line.qty_to_invoice = 0
                for delivery in order.picking_ids:
                    #aggiungo i contrassegni
                    values = {
                    'order_id': order.id,
                    'name': contrassegno.name,
                    'product_uom_qty': 1,
                    'product_uom': contrassegno.uom_id.id,
                    'product_id': contrassegno.id,
                    'is_delivery': True,
                    }
                    sol = self.env['sale.order.line'].create(values)
                    sol.product_id_change()
                    sol.qty_to_invoice  = 0
                    
                    for stock_move in delivery.move_lines_related:
                        self._set_order_to_invoice(stock_move,order)

                    self.set_delivery_to_invoice(delivery,order,contrassegno.id)
                    # for line in order.order_line:
                    #     print "line.qty_to_invoice %s" % line.qty_to_invoice
                    inv_lst += order.action_invoice_create()
                    # print "****************************************************"
                    # for line in order.order_line:
                    #     print "line.qty_to_invoice %s" % line.qty_to_invoice






            





    @api.one
    def _set_order_to_invoice(self,stock_move,order):

        prod_id = stock_move.product_id
        qty = stock_move.product_uom_qty
     #   print "SET ORDER TO INVOICE id: %s qty: %s" %(prod_id,qty)
        lines = [line for line in order.order_line if line.product_id == prod_id ]
        for line in lines:
            qty_to_invoice = qty if qty < line.product_uom_qty else line.product_uom_qty
     #       print "qty_to_invoice %s line.qty_to_invoice %s" %(qty_to_invoice,line.qty_to_invoice)
            line.qty_to_invoice += qty_to_invoice
     #       print "line.qty_to_invoice %s" % line.qty_to_invoice
            qty = qty - qty_to_invoice
     #       print "qty %s" % qty
            if qty <= 0:
                break

    @api.one
    def set_delivery_to_invoice(self,pick,order,cod_id):
        print "PICK carrier_price %s" %pick.carrier_price
        lines = [line for line in order.order_line if line.is_delivery and line.price_unit == pick.carrier_price and  line.qty_invoiced < line.product_uom_qty]
        # for line in order.order_line:
        #     print line.id
        #     if line.is_delivery:
        #         print "DELIVERY!"
        #         if line.price_unit == pick.carrier_price:
        #             print "PREZZO OK"
        #             if line.qty_invoiced < line.product_uom_qty:
        #                 print "QTY_TO_INVOICE OK"

        if lines:
            print "well done!"
            lines[0].qty_to_invoice = 1

        lines = [line for line in order.order_line if line.product_id.id == cod_id and line.qty_invoiced < line.product_uom_qty]

        print "YOOOO"
        print lines

        # for line in order.order_line:
        #     print line.id
        #     if line.product_id.id == cod_id:
        #         print "CONTRASSEGNO!"
        #         if line.qty_invoiced < line.product_uom_qty:
        #             print "QTY_TO_INVOICE OK"
        if lines:
            print "yo found!"
            lines[0].qty_to_invoice = 1


    @api.multi
    def execute(self):
        if self.csv_file:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.DictReader(decodedIO, delimiter=';')
            #implementing the head-tail design pattern
            head = reader.next()
            head = strip_keys(head)

            key = BRT if BRT in head else SDA
            money_key = MONEY_BRT if MONEY_BRT in head else MONEY_SDA
            warning_list = []
            contrassegno = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal')
            self._check_line(head,warning_list,key,money_key,contrassegno)

            for line in reader:
                #attenzione alle ultime due righe coi totali
                line = strip_keys(line)
                self._check_line(line,warning_list,key,money_key,contrassegno)


            if warning_list:
                raise Warning("non sono stati trovati pagamenti in contrassegno per i seguenti ordini nel file: %s" %warning_list)


    def _check_line(self,line, warning_list,key,money_key,contrassegno):
        found = False
        if line[key]:
            order = self.env["sale.order"].search([("name","=",line[key])])
            if order:
                for payment in order.account_payment_ids:
                    amount_str = line[money_key].replace(",",".").replace("€","")
                    if payment.amount == float(amount_str) and payment.journal_id == contrassegno:
                        payment.state = "posted"
                        found = True
                        break
                if not found:
                    warning_list.append(line[key])
