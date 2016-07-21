# -*- coding: utf-8 -*-

import csv

from datetime import date
from io import BytesIO

from openerp import api, models


class Cron(models.Model):
    _name = 'netaddiction_contributions.margin_calculator'

    @api.model
    def run(self):
        """"
        calcola i margini dei prodotti e degli ordini
    	"""
        orders = self.env['sale.order'].search([('is_complete_margin','=',False)])
        
        for order in orders:
            count += 1
            margin_new = 0
            marginate = 0
            for line in order.order_line:
                if line.margin_new == 0 and line.purchase_price_real == 0:
                    line._calculate_purchase_price_real()
                    line._calculate_product_margin()

                margin_new += line.margin_new

            if order.state == 'done':
                order.is_complete_margin = True
            
            order.margin_new = margin_new