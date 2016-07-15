# -*- coding: utf-8 -*-
from openerp.exceptions import Warning
from openerp import models, fields, api
from openerp.tools import float_compare, float_is_zero

class autopreparation(models.TransientModel):

    _inherit = "stock.picking.to.wave"

    @api.multi 
    def attach_pickings(self, values):
        #versione base, metto in lista le spedizioni segnate
        stocks = self.env['stock.picking'].search([('id','in',values['active_ids'])])
        error_stock = []
        subtype = self.env.ref('netaddiction_warehouse.error_autopreparation')
        
        for stock in stocks:
            note = []
            # se non è disponibile
            if stock.state != 'assigned':
                error_stock.append(stock.id)
                note.append('Non è disponibile.')
            #se ha già una lista
            if len(stock.wave_id) > 0:
                error_stock.append(stock.id)
                note.append('Ha già una lista associata.')
            #se non è in lavorazione o in parzialmente completato
            if stock.sale_id.state not in ['sale','partial_done']:
                error_stock.append(stock.id)
                note.append('L\'ordine non è in lavorazione o in parzialmente completato')
            #controllo indirizzo e valutazione cliente
            if stock.sale_id.partner_id.rating == 0:
                error_stock.append(stock.id)
                note.append('Rating cliente negativo')
            shipping_address = stock.sale_id.partner_shipping_id
            if not shipping_address.street  or not shipping_address.street2 or not shipping_address.city:
                error_stock.append(stock.id)
                note.append('Mancano dati nell\'indirizzo di spedizione')

            if stock.sale_id.customer_comment:
                error_stock.append(stock.id)
                note.append('Commento Cliente')

            attr = {
               'subject' : 'Errori autopreparazione',
               'message_type' : 'notification',
               'model' : 'stock.picking',
               'res_id' : stock.id,
               'body' : '<br/>'.join(note),
               'subtype_id' : subtype.id
            }
            self.env['mail.message'].create(attr)



        if len(error_stock) > 0:
            view_id = self.env['ir.ui.view'].search([('name','=','stock.vpicktree')])
            action = {
                'type': 'ir.actions.act_window',
                'res_model': "stock.picking",
                'view_id': view_id.id,
                'view_mode': 'tree,form',
                'target': 'current',
                'domain' : [('id','in',error_stock)],
                'context': {},
                'name' : 'Spedizioni con Errori'
            }
            return action
       
