# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import _
from openerp.exceptions import Warning


class Order(models.Model):
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

    ##############
    # ACTION STATE#
    ##############

    @api.one
    def action_problems(self):
        self.state = 'problem'

    @api.one
    def action_partial_done(self):
        self.state = 'partial_done'

    ##########
    # OVERRIDE#
    ##########

    # Toglie il controllo sullo stato 'draft' per l'aggiunta delle spese di spedizione
    @api.multi
    def delivery_set(self):
        pass

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id')
            # Search for refunds as well
            refund_ids = self.env['account.invoice'].browse()
            if invoice_ids:
                refund_ids = refund_ids.search([('type', '=', 'out_refund'), ('origin', 'in', invoice_ids.mapped('number')), ('origin', '!=', False)])

            line_invoice_status = [line.invoice_status for line in order.order_line]

            if order.state not in ('sale', 'done','partial_done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'


            order.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })



    @api.one
    def _send_cancel_mail(self):
        # TODO: modificare mittente e testo mail
        body_html = '''cancellato ordine'''
        values = {
            'subject': 'ordine cancellato',
            'body_html': body_html,
            'email_from': 'no-reply',
            'email_to': self.partner_id.email,
        }

        email = self.env['mail.mail'].create(values)
        email.send()

    @api.multi
    def action_done(self):
        for order in self:
            if self.account_payment_ids:
                all_paid = True
                for p in self.account_payment_ids:
                    all_paid = all_paid and p.state == 'posted'
                if all_paid:
                   super(Order, order).action_done()
                else:
                    raise Warning(_('I pagamenti non sono completati'))
            else:
                raise Warning(_('I pagamenti non sono completati'))


    @api.multi
    def _check_action_done(self):
        self.ensure_one()
        if all(line.qty_invoiced == line.qty_delivered == line.product_uom_qty for line in self.order_line):
            if (self.state == 'sale' or self.state == 'partial_done'):
                self.action_done()

    @api.multi
    def _check_partially_done(self):
        self.ensure_one()
        if (self.state == 'sale'):
                self.write({'state': 'partial_done'})

    def _check_offers_catalog(self):
        """controlla le offerte catalogo e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit per la sua offerta catalogo corrispondente
        False altrimenti
        """
        problems = False
        if( self.state == 'draft'):
            for line in self.order_line:
                if( line.offer_type and  not line.negate_offer ):
                    offer_line = line.product_id.offer_catalog_lines[0] if len(line.product_id.offer_catalog_lines) >0 else None
                    if offer_line:
                        offer_line.qty_selled += line.product_uom_qty
                        offer_line.active = offer_line.qty_limit == 0 or offer_line.qty_selled < offer_line.qty_limit
                    if(offer_line.qty_limit >0 and offer_line.qty_selled > offer_line.qty_limit):
                        problems = True

        return problems

    
    def _check_offers_cart(self):
        """controlla le offerte carrello e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit per la sua offerta carrello corrispondente
        False altrimenti
        """

        problems = False
        if( self.state == 'draft'):
            for och in self.offers_cart:

                    offer_line = och.offer_cart_line
                    if offer_line:
                        offer_line.qty_selled += och.qty
                        offer_line.active = offer_line.qty_limit == 0 or offer_line.qty_selled < offer_line.qty_limit
                    if(offer_line.qty_limit >0 and offer_line.qty_selled > offer_line.qty_limit):
                        problems = True

        return problems


    def _check_offers_vaucher(self):
        """controlla le offerte vaucher e aggiorna le quantità vendute.
        returns True se qualche prodotto ha superato la qty_limit per la sua offerta carrello corrispondente
        False altrimenti
        """

        problems = False
        if( self.state == 'draft'):
            for ovh in self.offers_vaucher:

                    offer = ovh.offer_id
                    if offer:
                        offer.qty_selled += ovh.qty
                        offer.active = offer.qty_limit == 0 or offer.qty_selled < offer.qty_limit
                    if(offer.qty_limit >0 and offer.qty_selled > offer.qty_limit):
                        problems = True

        return problems

    def _check_digital_bonus(self):

            if( self.state == 'draft'):
                for line in self.order_line:
                    for bonus_offer in line.product_id.code_ids:
                        codes =self.env["netaddiction.specialoffer.digital_code"].search([("bonus_id","=",bonus_offer.id),("sent","=",False),("order_id","=",None)])
                        if len(codes) > 0:
                            i = 0
                            while i < line.product_uom_qty:
                                code = codes[i]
                                code.order_id =self.id
                                code.order_line_id = line.id
                                i+=1
                        else:
                            #TODO MAIL a riccardo e commento
                            return

               


    @api.one
    def action_problems(self):
        self._check_offers_catalog()
        self._check_offers_cart()
        self._check_offers_vaucher()
        self._check_digital_bonus()
        self.state = 'problem'


    @api.multi
    def action_confirm(self):
        for order in self:
            problems = False
            problems = order._check_offers_catalog() 
            problems = order._check_offers_cart() or problems
            problems = order._check_offers_vaucher() or problems
            self._check_digital_bonus()
            #TODO se c'è un commento spostare in problem non in sale
            if problems or order.amount_total < 0:
            #TODO aggiungere il commento sul perchè
                order.state = 'problem'
            else:
                super(Order, order).action_confirm()
                if order.gift_discount > 0.0:
                    order.partner_id.remove_gift_value(order.gift_discount)
    
    @api.multi
    def action_cancel(self):
        #N.B. offerte mai riattivate manualmente
        self._send_cancel_mail()
        for order in self:
            if (order.state != 'draft'):
                #offerte catalogo
                for line in order.order_line:
                    if( line.offer_type  and not line.negate_offer):
                        offer_line = order.product_id.offer_catalog_lines[0] if len(order.product_id.offer_catalog_lines) >0 else None
                        if offer_line:
                            offer_line.qty_selled -= line.product_uom_qty
                #offerte carrello
                for och in order.offers_cart:
                    offer_line = och.offer_cart_line
                    if offer_line:
                        offer_line.qty_selled -= och.qty
                #ristorare gifts
                
                if order.gift_discount > 0.0:
                    order.partner_id.add_gift_value(order.gift_discount, "Rimborso")
                    

                
                #ristoro codici non mandati
                for code in self.code_ids:
                    if not code.sent:
                        code.order_id = None
                        code.order_line_id = None

                #qua annullo le spedizioni
                for pick in self.picking_ids:
                    pick.action_cancel()


        super(Order, self).action_cancel()

    @api.depends('order_line.price_total','gift_discount')
    def _amount_all(self):
        super(Order,self)._amount_all()
        for order in self:
            order._compute_gift_amount()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sale Order'),
        ('partial_done', 'Parzialmente Completato'),
        ('problem', 'Problema'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')

    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')


    @api.constrains('qty_delivered','qty_invoiced')
    def _check_complete(self):
        for line in self:
            if (line.qty_invoiced == line.qty_delivered == line.product_uom_qty):
                line.order_id._check_action_done()
            elif (line.qty_delivered > 0):
                line.order_id._check_partially_done()
 
    ##########
    # OVERRIDE#
    ##########

    # Aggiungo partial done agli stati in cui si può fatturare

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done','partial_done'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'


    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done', 'partial_done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
