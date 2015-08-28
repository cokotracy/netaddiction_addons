# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Wh_Locations(models.Model):
    _name = 'netaddiction.wh.locations'

    name = fields.Char(string="Nome",required="True")
    barcode = fields.Char(string="Barcode",size=10,required="True")
    wh_locations_line_ids = fields.One2many(comodel_name='netaddiction.wh.locations.line',
        inverse_name='wh_location_id',string='Allocazioni')
    company_id = fields.Many2one(comodel_name='res.company',string="Azienda",required="True")
    stock_location_id = fields.Many2one(comodel_name='stock.location',string="Magazzino",required="True")

class Product_Wh_Locations_Line(models.Model):
    _name = 'netaddiction.wh.locations.line'

    wh_location_id = fields.Many2one(comodel_name='netaddiction.wh.locations',
        string="Id Locazione",required="True")
    product_id = fields.Many2one(comodel_name='product.product',string="Id Prodotto",required="True")
    qty = fields.Integer('Quantità',required="True",default=1)

class Products(models.Model):
    _inherit = 'product.product'

    product_wh_location_line_ids = fields.One2many(comodel_name='netaddiction.wh.locations.line',
        inverse_name='product_id',string='Allocazioni')
