# -*- coding: utf-8 -*-
import csv
import base64
import io
from openerp import models, fields, api
from openerp.exceptions import Warning



class DigitalBonus(models.Model):
    
    _name = "netaddiction.specialoffer.digital_bonus"

    csv_file = fields.Binary('File')

    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=True)
    name = fields.Char(string='Titolo', required=True)
    products_ids = fields.Many2many('product.product', 'prod_codes_rel', 'code_id', 'prod_id', 'Prodotti')
    code_ids = fields.One2many('netaddiction.specialoffer.digital_code','bonus_id', string='Codici associati')
    text = fields.Text("testo offerta")
    csv_file = fields.Binary('File')


    @api.one
    def process_file(self):
        if self.csv_file:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.reader(decodedIO)
            #implementing the head-tail design pattern

             


            for line in reader:
                if not self.env["netaddiction.specialoffer.digital_code"].search([("bonus_id","=",self.id),("code","=",line[0])]):
                    self.env["netaddiction.specialoffer.digital_code"].create({'code':line[0],'order_id':None,'bonus_id':self.id,'sent':False,'date_sent':None,'sent_by':None})

            self.csv_file = None

            

        else:
            raise Warning("nessun file selezionato")

class DigitalCode(models.Model):

    _name = "netaddiction.specialoffer.digital_code"

    code = fields.Char(string='Codice', required=True)
    order_id = fields.Many2one('sale.order', string='Ordine collegato', default=None)
    bonus_id = fields.Many2one('netaddiction.specialoffer.digital_bonus', string='offerta collegato', default=None)
    sent = fields.Boolean(string="Spedito", default=False)
    date_sent = fields.Datetime('Data spedizione')
    sent_by = fields.Many2one(comodel_name='res.users',string='Spedito da')


class DigitalProducts(models.Model):

    _inherit = 'product.product'

    code_ids = fields.Many2many('netaddiction.specialoffer.digital_bonus', 'prod_codes_rel',  'prod_id', 'code_id','Codici Digitali')

class DigitalOrders(models.Model):

    _inherit = 'sale.order'

    code_ids = fields.One2many('netaddiction.specialoffer.digital_code','order_id', string='Codici associati')