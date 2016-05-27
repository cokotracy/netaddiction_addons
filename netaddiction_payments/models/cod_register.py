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
    		contrassegno = self.env["account.journal"].search([("name","=","Contrassegno")])
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
    			print "here"
    			for payment in order.account_payment_ids:
    				amount_str = line[money_key].replace(",",".").replace("€","")
    				if payment.amount == float(amount_str) and payment.journal_id == contrassegno:
    					print "reconcilhere"
    					payment.state = "posted"
    					found = True
    					break
    			if not found:
    				warning_list.append(line[key])
