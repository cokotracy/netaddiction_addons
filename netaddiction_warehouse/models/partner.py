# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Supplier(models.Model):
    _inherit="res.partner"

    supplier_priority = fields.Selection([('0','0'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('6','6'),('8','8'),('9','9'),('10','10')],help="Priorità fornitore: più alta è la priorità più verrà preso in considerazine per gli ordini e le disponibilità prodotto",string="Priorità Fornitore",default="9")
    supplier_delivery_time = fields.Integer(string="Tempo di consegna del fornitore",default=1)
