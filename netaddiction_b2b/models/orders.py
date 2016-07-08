# -*- coding: utf-8 -*-

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

class Orders(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def simulate_delivery_price(self,subdivision):
    	self.ensure_one()
    	if self.pricelist_id.id != 1:
    		pass
    	else:
    		return super(Orders,self).simulate_delivery_price(subdivision)