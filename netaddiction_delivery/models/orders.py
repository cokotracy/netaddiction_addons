# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class Orders(models.Model):
	delivery_option = fields.Selection([('all', 'In una unica spedizione'), ('asap', 'Man mano che i prodotti sono disponibili')],
                                       string='Opzione spedizione')
    @api.multi
    def action_confirm(self):
        super(OrdersReverse,self).action_confirm()

        for so in self:
            #se il cliente ha deciso che non l'ordini deve essere spedito tutto insieme
            if so.delivery_option == 'all':
                self._proceed_not_splittable()
                
    @api.multi
    def _proceed_not_splittable(self):
        """
        Se l'ordine non è splittabile allora devo attendere tutte le disponibilità dei prodotti
        """
        for pick in self.picking_ids:
            #e se lo stato delle sue spedizioni è 'parzialmente disponibile', 
            #ossia c'è almeno un prodotto in attesa disponibilità
            if pick.state == 'partially_available':
                for move in pick.move_lines_related:
                    if move.state == 'assigned':
                        move.state = 'waiting'
                #allora metto la spedizione in waiting
                pick.state = 'waiting'

    @api.one
    def delivery_gratis(self):
        """
        chiamando questa funzione si azzerano le spese di spedizione
        deve essere sempre settato il carrier_id e prima di operare richiama delivery_set()
        così che venga settato già il metodo di spedizione con i suoi calcoli
        """
        #richiamo delivery_set, non si sa mai.
        self.delivery_set()
        carrier_line = self.env['sale.order.line'].search([('order_id','=',self.id),('is_delivery','=',True)])
        carrier_line.write({'price_unit': 0.00})
        self.write({'delivery_price' : 0.00})
        return True    