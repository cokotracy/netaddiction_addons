# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class Orders(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Nuovo'),
        ('sent', 'Preventivo Inviato'),
        ('sale', 'In Lavorazione'),
        ('partial_done', 'Parzialmente Completato'),
        ('problem', 'Problema'),
        ('done', 'Completato'),
        ('cancel', 'Annullato'),
        ], string='Status', readonly=True, copy=False, index=True)

    ip_address = fields.Char(string="Indirizzo IP")
    delivery_option = fields.Selection([('all','tutto insieme'),('asap','non appena disponibile')], string='Opzione spedizione')

    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)], 'sale': [('readonly', True)], 'partial_done': [('readonly', True)]}, copy=True)



    ##############
    #ACTION STATE#
    ##############

    @api.one 
    def action_problems(self):
        self.state = 'problem'

    @api.one 
    def action_partial_done(self):
        self.state = 'partial_done'

    ##########
    #OVERRIDE#
    ##########

    #Toglie il controllo sullo stato 'draft' per l'aggiunta delle spese di spedizione
    @api.multi
    def delivery_set(self):
        # Remove delivery products from the sale order
        self._delivery_unset()

        for order in self:
            carrier = order.carrier_id
            if carrier:
                #if order.state not in ('draft', 'sent'):
                #    raise UserError(_('The order state have to be draft to add delivery lines.'))

                if carrier.delivery_type not in ['fixed', 'base_on_rule']:
                    # Shipping providers are used when delivery_type is other than 'fixed' or 'base_on_rule'
                    price_unit = order.carrier_id.get_shipping_price_from_so(order)[0]
                else:
                    # Classic grid-based carriers
                    carrier = order.carrier_id.verify_carrier(order.partner_shipping_id)
                    if not carrier:
                        raise UserError(_('No carrier matching.'))
                    price_unit = carrier.get_price_available(order)
                    if order.company_id.currency_id.id != order.pricelist_id.currency_id.id:
                        price_unit = order.company_id.currency_id.with_context(date=order.date_order).compute(price_unit, order.pricelist_id.currency_id)

                order._create_delivery_line(carrier, price_unit)

            else:
                raise UserError(_('No carrier set for this order.'))

    @api.multi
    def action_cancel(self):
        self._send_cancel_mail()
        super(Orders, self).action_cancel()

    @api.multi
    def action_confirm(self):
        # TODO: verificare il campo delivery_option
        super(Orders, self).action_confirm()

    @api.one
    def _send_cancel_mail(self):
        print self.partner_id.email
        # TODO: modificare mittente e testo mail
        body_html = '''cancellato ordine'''
        values = {
            'subject' : 'ordine cancellato',
            'body_html': body_html,
            'email_from' : 'no-reply',
            'email_to' : self.partner_id.email,
        }

        email = self.env['mail.mail'].create(values)
        email.send()


        

