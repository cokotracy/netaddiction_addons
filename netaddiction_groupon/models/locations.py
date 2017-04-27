# -*- coding: utf-8 -*-
from openerp import models, fields, api

class GrouponLocations(models.Model):
    _name = 'groupon.wh.locations'
    _inherit = 'netaddiction.wh.locations'

class GrouponWhLocationsLine(models.Model):
    _name = 'groupon.wh.locations.line'
    _inherit = 'netaddiction.wh.locations.line'

class GrouponProducts(models.Model):
    _inherit = 'product.product'

    groupon_wh_location_line_ids = fields.One2many(
        comodel_name='groupon.wh.locations.line',
        inverse_name='product_id',
        string='Allocazioni Groupon')
