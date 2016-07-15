# -*- coding: utf-8 -*-
from openerp.exceptions import Warning
from openerp import models, fields, api
from openerp.tools import float_compare, float_is_zero

class Autopreparation_b2b(models.TransientModel):

    _inherit = "stock.picking.to.wave"

    @api.multi 
    def attach_pickings(self, values):
        pass
        ##versione base, metto in lista le spedizioni segnate
        #stocks = self.env['stock.picking'].search([('id','in',values['active_ids'])])
        #error_stock = []
        #partner = stocks[0].partner_id
        #for stock in stocks:
        #    if partner != stock.partner_id:
        #        raise Warning("Stai unendo clienti B2B differenti.")
        #    # se non è disponibile
        #    if stock.state != 'assigned':
        #        error_stock.append(stock.id)
        #    #se ha già una lista
        #    if len(stock.wave_id) > 0:
        #        error_stock.append(stock.id)
        #    #se non è in lavorazione o in parzialmente completato
        #    if stock.sale_id.state not in ['sale','partial_done']:
        #        error_stock.append(stock.id)
        #   
#
        #if len(error_stock) > 0:
        #    view_id = self.env['ir.ui.view'].search([('name','=','stock.vpicktree')])
        #    action = {
        #        'type': 'ir.actions.act_window',
        #        'res_model': "stock.picking",
        #        'view_id': view_id.id,
        #        'view_mode': 'tree,form',
        #        'target': 'current',
        #        'domain' : [('id','in',error_stock)],
        #        'context': {},
        #        'name' : 'Spedizioni con Errori'
        #    }
        #    return action
        #



