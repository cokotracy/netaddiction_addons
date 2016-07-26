# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
import datetime
import pickle
import base64
import os

import StringIO

class NetaddictionManifest(models.Model):
    _name = 'netaddiction.manifest'

    _rec_name = 'date'

    _order = 'date desc'

    delivery_ids = fields.One2many(string="Spedizioni",comodel_name="stock.picking",inverse_name="manifest")
    manifest_file1 = fields.Binary(string="File1", attachment=True)
    manifest_file2 = fields.Binary(string="File2", attachment=True)
    date = fields.Date(string="Data Manifest")
    carrier_id = fields.Many2one(string="Corriere",comodel_name="delivery.carrier")

    @api.one 
    def send_manifest(self):
        if 'Bartolini' in self.carrier_id.name:
            if self.manifest_file1 is None or self.manifest_file2 is None: 
                raise ValidationError("Non hai ancora creato il manifest")
        else:
            if self.manifest_file1 is None:
                raise ValidationError("Non hai ancora creato il manifest")

    @api.one 
    def create_manifest(self):
        if 'Bartolini' in self.carrier_id.name:
            self.create_manifest_bartolini()
        else:
            self.create_manifest_sda()

    @api.multi
    def create_manifest_sda(self):
        self.ensure_one()

        result = self.env['ir.values'].search([('name','=','contrassegno_id')])
        payment_contrassegno = False
        for r in result :
            payment_contrassegno = int(r.value)

        if payment_contrassegno is False:
            raise ValidationError("Non sono state effettuate le configurazioni del Manifest SDA")

        name1 = datetime.datetime.now().strftime('%Y%m%d%H%M')
        
        file1 = StringIO.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                payment = delivery.sale_order_payment_method

                riga = 'CLI120522416' #CODICE IDENTIFICATIVO
                riga += ' '*30 
                riga += 'NN'
                riga += 'S' #stampa ldv
                riga += delivery.delivery_barcode #numero spedizione
                count = 25 - len(delivery.delivery_barcode)
                riga += ' '*count
                riga += datetime.date.today().strftime('%Y%m%d')
                riga += 'P'
                riga += 'NETA30'
                riga += ' '*14
                azienda = 'NetAddiction srl'
                riga += azienda
                count = 40 - len(azienda)
                riga += ' '*count
                capo = 'Riccardo Ioni'
                riga += capo
                count = 20 - len(capo)
                riga += ' '*count
                riga += 'Via  '
                via = 'A.M.Angelini'
                riga += via
                count = 30 - len(via)
                riga += ' '*count
                riga += '12'
                riga += ' '*3
                tel = '07442462'
                riga += tel
                count = 15 - len(tel)
                riga += ' '*count
                cap = '05100'
                riga += cap
                count = 9-len(cap)
                riga += ' '*count
                citta = "Terni"
                riga += citta
                count = 30 - len(citta)
                riga += ' '*count
                riga += 'TR'
                riga += ' '*18
                company = delivery.sale_id.partner_shipping_id.company_address[0:40]
                riga += company
                count = 40-len(company)
                riga += ' '*count
                name = delivery.sale_id.partner_shipping_id.name[0:20]
                riga += name
                count = 20 - len(name)
                riga += ' '*count
                address = delivery.sale_id.partner_shipping_id.street + ' ' + delivery.sale_id.partner_shipping_id.street2
                address = address[0:40]
                riga += address
                count = 40 - len(address)
                riga += ' '*count
                mobile = delivery.sale_id.partner_id.mobile.replace(' ','')
                mobile = mobile.replace('+39','')
                mobile = mobile[0:15]
                riga += mobile
                count = 15 - len(mobile)
                riga += ' '*count
                cap = delivery.sale_id.partner_shipping_id.zip[0:9]
                riga += cap
                count = 9 - len(cap)
                riga += ' '*count
                citta = delivery.sale_id.partner_shipping_id.city[0:30]
                riga += citta
                count = 30 - len(citta)
                riga += ' '*count
                riga += delivery.sale_id.partner_shipping_id.state_id.code 
                count = 2 - len(delivery.sale_id.partner_shipping_id.state_id.code)
                riga += ' '*count
                riga += "001"
                riga += "0001000"
                riga += '0'*15
                riga += 'EXT'
                riga += ' '*40
                riga += 'EU'

                if payment:
                    if payment.id == payment_contrassegno:
                        t = str(round(delivery.total_import,2))
                        split = t.split('.')
                        c = 2 - len(split[1])
                        total = split[0]+'.'+split[1]+'0'*c
                        total = total.zfill(9)
                        riga += total
                        riga += 'CON'
                    else:
                        riga += ' '*12
                else:
                    riga += ' '*12

                riga += ' '*30
                riga += "0000516.46"
                riga += delivery.delivery_barcode #numero spedizione
                count = 25 - len(delivery.delivery_barcode)
                riga += ' '*count
                riga += 'TR'
                riga += 'Varie'
                count = 30 - len('Varie')
                riga += ' '*count
                riga += 'P'
                riga += ' '*3
                riga += ' '*3
                riga += ' '*10
                riga += 'MGCS'
                riga += ' '*5
                riga += ' '
                riga += '03'
                riga += ' '*20
                riga += '\r\n'
                file1.write(riga)

        
        self.manifest_file1 = base64.b64encode(file1.getvalue())
        self.manifest_file2 = None
        
        file1.close()

    @api.multi
    def create_manifest_bartolini(self):
        self.ensure_one()
        
        #RECUPERO I SETTINGS
        prefix1 = False
        prefix2 = False
        
        payment_contrassegno = False

        result = self.env['ir.values'].search([('name','=','bartolini_prefix_file1')])
        for r in result:
            prefix1 = r.value
        result = self.env['ir.values'].search([('name','=','bartolini_prefix_file2')])
        for r in result:
            prefix2 = r.value
        
        result = self.env['ir.values'].search([('name','=','contrassegno_id')])
        for r in result:
            payment_contrassegno = int(r.value)

        if prefix1 is False or prefix2 is False or payment_contrassegno is False:
            raise ValidationError("Non sono state effettuate le configurazioni del Manifest Bartolini")

        #CREO I FILES
        name1 = prefix1 + self.date.replace("-","") + ".txt"
        file1 = StringIO.StringIO()
        #name2 = prefix2 + self.date.replace("-","") + ".txt"
        #file2 = StringIO.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                payment = delivery.sale_order_payment_method

                file1.write("  ") #flag annullamento
                file1.write("0270443 ") #nostro codice
                file1.write("026 ") # Punto operativo di partenza
                file1.write(datetime.datetime.strptime(self.date,"%Y-%m-%d").strftime("%Y")) #anno
                file1.write(" ") #spazi
                file1.write("00") #numero serie
                file1.write(" ") #spazi
                file1.write(delivery.delivery_barcode[6:]) #id spedizione univoco
                
                if payment:
                    if payment.id == payment_contrassegno:
                        file1.write("4 ") #se contrassegno
                    else:
                        file1.write("1 ") #tutti gli altri pagamenti
                else:
                    file1.write("1 ")

                file1.write(" 000")
                name = delivery.sale_id.partner_shipping_id.name + ' ' + delivery.sale_id.partner_shipping_id.company_address
                if len(name)>69:
                    file1.write(name[0:69]) #prima parte destinatario
                else:
                    file1.write(name) #prima parte destinatario
                
                count = 70-len(name)
                spaces = ' '*count
                file1.write(spaces) #seconda parte destinatario

                address = delivery.sale_id.partner_shipping_id.street + ' ' + delivery.sale_id.partner_shipping_id.street2
                address = address[0:35]
                file1.write(address) #indirizzo
                count = 35 - len(address)
                spaces = ' '*count
                file1.write(spaces) #indirizzo

                cap = delivery.sale_id.partner_shipping_id.zip[0:9]
                file1.write(cap) #CAP
                count = 9 - len(cap)
                spaces = ' '*count
                file1.write(spaces) #CAP

                citta = delivery.sale_id.partner_shipping_id.city[0:35]
                file1.write(citta) #citta
                count = 35 - len(citta)
                spaces = ' '*count
                file1.write(spaces) #citta

                provincia = delivery.sale_id.partner_shipping_id.state_id.code 
                file1.write(provincia) #provincia
                
                file1.write("   ") #italia
                file1.write("  ") #primo giorno di chiusura
                file1.write("  ") #secondo giorno di chiusura
                file1.write(" 300") #codice tariffa
                file1.write("C") #tipo servizio bolle

                file1.write(" 0000000000,000") #importo da assicurare
                file1.write("EUR") #currency
                file1.write("Videogiochi    ") #tipo merce
                file1.write(" 00001") #numero colli
                file1.write(" ")

                weight = '1,0'
                count = 8 - len(weight)
                zeros = '0'*count
                file1.write(zeros)
                file1.write(weight) # peso
                file1.write(" 00,000") #volume
                file1.write(" 0000000000,000") #quantità da fatturare

                if payment:
                    if payment.id == payment_contrassegno:
                        file1.write(" ")
                        t = str(round(delivery.total_import,2))
                        split = t.split('.')
                        c = 3 - len(split[1])

                        total = split[0]+','+split[1]+'0'*c 
                        count = 14 - len(total)
                        zeros = '0'*count
                        file1.write(zeros)
                        file1.write(total) #importo contrassegno
                        file1.write("  ") #tipo incasso contrassegno
                        file1.write("EUR") #currency
                    else:
                        file1.write(" 0000000000,000") #importo
                        file1.write("  ") #tipo incasso contrassegno
                        file1.write("   ") #divisa contrassegno
                else:
                    file1.write(" 0000000000,000") #importo
                    file1.write("  ") #tipo incasso contrassegno
                    file1.write("   ") #divisa contrassegno

                file1.write("   ")
                file1.write(str(delivery.sale_id.name).zfill(15)) #idordine
                file1.write("               ") #rferimento alfanumerico
                file1.write(" 0000000") #dal numero
                file1.write(" 0000000") #al numero
                file1.write(" ") #blank fisso

                file1.write(" "*35) #note???
                file1.write(" "*35) #note2???
                file1.write(" 00") # zona di consegna
                file1.write("7Q") #cod.trattamento merce
                file1.write(" ") #ritiro c/deposito
                file1.write(" 00000000") #fata consegna richiesta
                file1.write(" ") #tipo consegna richiesta
                file1.write(" 0000") #ora richiesta
                file1.write("  ") #tipo tassazione
                file1.write(" ") #flag tariffa
                file1.write(" 0000000000,000") #valore dichiarato
                file1.write("EUR") #currency
                file1.write("  ") #particolarità di consegna
                file1.write("  ") #particolarità di giacenza
                file1.write("  ") #particolarità varie
                file1.write(" ") #1a consegna particolare
                file1.write(" ") #2a consegna particolare
                file1.write(" ") #codice sociale
                file1.write(" 000000000") #tipo bancali
                file1.write("                         ") #mittente
                file1.write("         ") #cap
                file1.write("   ") #nazione
                file1.write("\r\n") 
            
            
        self.manifest_file1 = base64.b64encode(file1.getvalue())
        file1.close()

        file2 = StringIO.StringIO()

        for delivery in self.delivery_ids:
            if delivery.delivery_read_manifest:
                #secondo file
                file2.write("  ") #flag annullamento
                file2.write("0270443 ") #nostro codice
                file2.write("026 ") #punto operativo di partenza
                file2.write(datetime.datetime.strptime(self.date,"%Y-%m-%d").strftime("%Y")) #anno di spedizione
                file2.write(" ") #spazio
                file2.write("00") 
                file2.write(" ")
                file2.write(delivery.delivery_barcode[6:]) #id spedizione univoco
                file2.write("E") #tipo record testa
                file2.write(delivery.delivery_barcode) 
                file2.write("\r\n")

                file2.write("  ")
                file2.write("0270443 ") #nostro codice
                file2.write("026 ") #punto partenza
                file2.write(datetime.datetime.strptime(self.date,"%Y-%m-%d").strftime("%Y")) #anno di spedizione
                file2.write(" ") #spazio
                file2.write("00") 
                file2.write(" ")
                file2.write(delivery.delivery_barcode[6:]) #id spedizione univoco
                file2.write("B") #tipo record test
                tel = delivery.partner_id.mobile[0:35]
                count = 35 - len(tel)
                file2.write(tel)
                file2.write(" "*count)
                file2.write("\r\n")

                file2.write("  ")
                file2.write("0270443 ") #nostro codice
                file2.write("026 ") #punto partenza
                file2.write(datetime.datetime.strptime(self.date,"%Y-%m-%d").strftime("%Y")) #anno di spedizione
                file2.write(" ") #spazio
                file2.write("00") 
                file2.write(" ")
                file2.write(delivery.delivery_barcode[6:]) #id spedizione univoco
                file2.write("I") #tipo record test
                email = delivery.partner_id.email[0:35]
                file2.write(email)
                file2.write(" ")
                file2.write("\r\n")

        self.manifest_file2 = base64.b64encode(file2.getvalue())
        file2.close()



class ManifestSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'netaddiction.manifest.settings'

    bartolini_prefix_file1 = fields.Char(string="Prefisso File1 Bartolini")
    bartolini_prefix_file2 = fields.Char(string="Prefisso File2 Bartolini")
    

    contrassegno_id = fields.Many2one(string="Metodo di pagamento per contrassegno",comodel_name="account.journal")


    @api.one
    def set_contrassegno_id(self,values):
        self.env['ir.values'].create({'name':'contrassegno_id','value':self.contrassegno_id.id,'model':'netaddiction.manifest.settings'})

    @api.one
    def set_bartolini_prefix_file1(self,values):
        self.env['ir.values'].create({'name':'bartolini_prefix_file1','value':self.bartolini_prefix_file1,'model':'netaddiction.manifest.settings'})

    @api.one
    def set_bartolini_prefix_file2(self,values):
        self.env['ir.values'].create({'name':'bartolini_prefix_file2','value':self.bartolini_prefix_file2,'model':'netaddiction.manifest.settings'})


    @api.model
    def get_default_values(self,fields):
        values = self.env['ir.values'].search([('model','=','netaddiction.manifest.settings')])
        attr = {
            'bartolini_prefix_file1' : '',
            'bartolini_prefix_file2' : '',
            'contrassegno_id' : '',
        }
        for v in values:
            attr[v.name] = v.value
            if v.name == 'contrassegno_id':
                attr[v.name] = int(v.value)
        return attr
        