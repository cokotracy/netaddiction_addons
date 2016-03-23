# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class OpSettings(models.Model):
    _name = 'netaddiction.warehouse.operations.settings'

    company_id = fields.Many2one(comodel_name="res.company",string="Azienda",ondelete="restrict",required="True")
    operation = fields.Many2one(comodel_name="stock.picking.type",string="Operazione di Magazzino", ondelete="restrict")
    netaddiction_op_type = fields.Selection(string="Tipo di Operazione",selection=[('reverse_scrape','Reso Difettati'),('reverse_resale','Reso Rivendibile'),('reverse_supplier','Reso a Fornitore'),('reverse_supplier_scraped','Reso a Fornitore Difettati')])
    