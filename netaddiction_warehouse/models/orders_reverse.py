# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class OrdersReverse(models.Model):
    _inherit = "sale.order"

    count_reverse = fields.Integer(string="# Resi",compute="_count_reverse")

    @api.one
    def _count_reverse(self):
        picking_type_id = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','=','reverse_scrape'),('company_id','=',self.env.user.company_id.id)])
        picking = self.env['stock.picking'].search([('origin','=',self.name),('picking_type_id','=',picking_type_id.operation.id)])
        self.count_reverse = len(picking)
