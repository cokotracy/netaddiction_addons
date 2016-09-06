# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from float_compare import isclose

class Order(models.Model):
    _inherit = 'sale.order'

    payment_method_id = fields.Many2one('account.journal', string='Metodo di pagamento')
    payment_method_name = fields.Char(related='payment_method_id.name', string='Nome Pagamento')
    pay_pal_tran_id = fields.Char(string='ID transazione paypal')
    cc_selection = fields.Many2one('netaddiction.partner.ccdata', string='Carta di credito')

    @api.multi
    def manual_confirm(self):
        """Metodo per l'interfaccia grafica del BO.

        (viene messo in vista in netaddiction orders).
        effettua la action confirm, crea fatture e pagamenti
        """
        for order in self:
            if order.state not in ('draft', 'pending'):
                # raise ValidationError("ordine non in draft")
                return False

            if not order.payment_method_id:
                raise ValidationError("nessun metodo di pagamento selezionato")

            cc_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'cc_journal')
            pp_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal')
            contrassegno_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal')
            zero_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'zeropay_journal')
            cash_journal = self.env['account.journal'].search([('code', '=', 'CSH1')])

            if order.payment_method_id.id not in [cc_journal.id, pp_journal.id, contrassegno_journal.id, cash_journal.id, zero_journal.id]:
                raise ValidationError("metodo di pagamento non valido")

            if order.payment_method_id.id == cc_journal.id and not order.cc_selection:
                raise ValidationError("Selezionare una carta di credito")

            if order.payment_method_id.id == pp_journal.id and not order.pay_pal_tran_id:
                raise ValidationError("Inserire un ID  transazione paypal")

            if not isclose(order.amount_total, 0.0) and order.payment_method_id.id == zero_journal.id:
                raise ValidationError("Non è un ordine a costo zero!")

            order.action_confirm()
            transient = None

            if isclose(order.amount_total, 0.0) or order.payment_method_id.id == zero_journal.id:
                transient = self.env["netaddiction.zeropayment.executor"].create({})
                transient.set_order_zero_payment(order)

            else:
                if order.payment_method_id.id == cc_journal.id:
                    transient = self.env["netaddiction.positivity.executor"].create({})
                    transient._generate_invoice_payment(order.id, order.cc_selection.token)
                if order.payment_method_id.id == pp_journal.id:
                    transient = self.env["netaddiction.paypal.executor"].create({})
                    transient._register_payment(order.partner_id.id, order.amount_total, order.id, order.pay_pal_tran_id)
                if order.payment_method_id.id == contrassegno_journal.id:
                    transient = self.env["netaddiction.cod.register"].create({})
                    transient.set_order_cash_on_delivery(order.id)
                if order.payment_method_id.id == cash_journal.id:
                    transient = self.env["netaddiction.cash.executor"].create({})
                    transient.register_cash_payment(order.partner_id.id, order.amount_total, order.id)

            if transient:
                transient.unlink()

    @api.multi
    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """Dominio sulle carte di credito del cliente."""
        res = super(Order, self).onchange_partner_id()
        if self.partner_id:
            cards = self.env["netaddiction.partner.ccdata"].search([('customer_id', '=', self.partner_id.id)])
            cards = [card.id for card in cards]
            if res:
                res['domain']['cc_selection'] = [('id', 'in', cards), ]
            else:
                domain = {'cc_selection': [('id', 'in', cards), ]}
                res = {}
                res['domain'] = domain
        return res


class OrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_payment = fields.Boolean(string="Is a Payment", default=False)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_id = fields.Many2one('account.payment', string='Pagamento', default=None)
