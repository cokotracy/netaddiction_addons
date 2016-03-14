# -*- coding: utf-8 -*-


from openerp import models, fields, api

class ExtraData(models.Model):
    _name = 'netaddiction.extradata.key.value'

    company_id = fields.Many2one(comodel_name='res.company', string="Azienda", required=True)
    value = fields.Char(string="Valore",required=True)
    key = fields.Char(string="Chiave", required=True)
    product_id = fields.Many2one(string="Prodotto",comodel_name="product.product", required=True)
    key_type = fields.Char(string="Tipo/Sito")

class Products(models.Model):
    _inherit = "product.product"

    extra_data = fields.One2many(string="Extra_Data", comodel_name="netaddiction.extradata.key.value", inverse_name="product_id")