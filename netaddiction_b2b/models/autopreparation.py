# -*- coding: utf-8 -*-
from openerp.exceptions import Warning
from openerp import models, fields, api
from openerp.tools import float_compare, float_is_zero
import datetime

class WaveB2B(models.Model):
    _inherit = "stock.picking.wave"

    @api.multi
    def put_in_manifest(self):
        for s in self:
            for pick in s.picking_ids:
                now = datetime.date.today()
                #cerco la presenza di un manifest
                manifest = self.env['netaddiction.manifest'].search([('date','=',now),('carrier_id','=',pick.carrier_id.id)])
                if len(manifest)==0:
                    #manifest per questo corriere non presente
                    man_id = self.env['netaddiction.manifest'].create({'date':now,'carrier_id':pick.carrier_id.id}).id
                else:
                    man_id = manifest.id

                pick.write({'manifest':man_id,'delivery_read_manifest':False})
                break

                


class Autopreparation_b2b(models.TransientModel):

    _inherit = "stock.picking.to.wave"

    @api.multi 
    def attach_pickings(self, values):
        stocks = self.env['stock.picking'].search([('id','in',values['active_ids'])])
        error_stock = []
        subtype = self.env.ref('netaddiction_warehouse.error_autopreparation')
        b2b = []
        not_b2b = []
        for stock in stocks:
            if stock.sale_id.is_b2b:
                b2b.append(stock)
            else:
                not_b2b.append(stock)

        if len(b2b) == 0:
            return super(Autopreparation_b2b,self).attach_pickings(values)
       
        if len(not_b2b)>0 and len(b2b) > 0:
            raise Warning('Non puoi processare ordini b2b e retail contemporaneamente')
 
        partner_base = stock[0].partner_id
        for stock in b2b:
            if stock.partner_id.id != partner_base.id:
                raise Warning('Non puoi processare ordini b2b di diversi clienti contemporaneamente')


        for stock in b2b:
            note = []
            pay = True
            # se non è disponibile
            if stock.state != 'assigned':
                error_stock.append(stock.id)
                note.append('Non è disponibile.')
                pay = False
            #se ha già una lista
            if len(stock.wave_id) > 0:
                error_stock.append(stock.id)
                note.append('Ha già una lista associata.')
                pay = False
            #se non è in lavorazione o in parzialmente completato
            if stock.sale_id.state not in ['sale','partial_done']:
                error_stock.append(stock.id)
                note.append('L\'ordine non è in lavorazione o in parzialmente completato')
                pay = False
            #controllo indirizzo e valutazione cliente
            if stock.sale_id.partner_id.rating == 0:
                error_stock.append(stock.id)
                note.append('Rating cliente negativo')
                pay = False

            shipping_address = stock.sale_id.partner_shipping_id
            if not shipping_address.street  or not shipping_address.street2 or not shipping_address.city:
                error_stock.append(stock.id)
                note.append('Mancano dati nell\'indirizzo di spedizione')
                pay = False

            # if stock.sale_id.customer_comment:
            #    error_stock.append(stock.id)
            #    note.append('Commento Cliente')
            #    pay = False

            if len(note)>0:
                attr = {
                   'subject' : 'Errori autopreparazione',
                   'message_type' : 'notification',
                   'model' : 'stock.picking',
                   'res_id' : stock.id,
                   'body' : '<br/>'.join(note),
                   'subtype_id' : subtype.id
                }
                self.env['mail.message'].create(attr)

        if len(error_stock) == 0:
            for b in b2b:
                b.write({'wave_id': self.wave_id.id})

            self.env['stock.picking'].invoice_single(b2b,b2b[0].partner_id.id)
        else:
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
        
       
        

