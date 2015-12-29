# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class Orders(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Preventivo'),
        ('sent', 'Preventivo Inviato'),
        ('sale', 'In attesa'),
        ('processing', 'In Lavorazione'),
        ('partial_done', 'Parzialmente Completato'),
        ('problem', 'Problema'),
        ('done', 'Completato'),
        ('cancel', 'Annullato'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='sale')
    
    ###################
    #BYPASS PREVENTIVI#
    ###################
    @api.model
    def create(self,values):
        order = super(Orders,self).create(values)
        #controllare per importazione
        if 'state' not in values.keys():
            order.action_confirm()
        return order

    ##############
    #ACTION STATE#
    ##############
    @api.one 
    def action_processing(self):
        self.state = 'processing'

    @api.one 
    def action_problem(self):
        self.state = 'problem'


