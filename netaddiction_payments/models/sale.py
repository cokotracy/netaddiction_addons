# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from float_compare import isclose



class Order(models.Model):
    _inherit = 'sale.order'

    payment_method_id = fields.Many2one('account.journal', string='Metodo di pagamento')
    payment_method_name = fields.Char(related='payment_method_id.name', string='Nome Pagamento')
    pay_pal_tran_id = fields.Char(string='ID transazione paypal')
    cc_selection = fields.Many2one('netaddiction.partner.ccdata', string='Carta di credito')


    @api.one
    def manual_confirm(self):
    	""" metodo per l'interfaccia grafica del BO. (viene messo in vista in netaddiction orders).
    		effettua la action confirm, crea fatture e pagamenti
    	"""

    	if not self.state == 'draft':
       		raise ValidationError("ordine non in draft")

        if not self.payment_method_id:
        	raise ValidationError("nessun metodo di pagamento selezionato")

        cc_journal  = self.env['ir.model.data'].get_object('netaddiction_payments','cc_journal')
        pp_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'paypal_journal')
        contrassegno_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'contrassegno_journal')
        zero_journal = self.env['ir.model.data'].get_object('netaddiction_payments', 'zeropay_journal')
        cash_journal = self.env['account.journal'].search([('code','=','CSH1')])
        

        if self.payment_method_id.id not in [cc_journal.id,pp_journal.id,contrassegno_journal.id,cash_journal.id,zero_journal.id]:
        	raise ValidationError("metodo di pagamento non valido")

        if self.payment_method_id.id == cc_journal.id and not self.cc_selection:
        	raise ValidationError("Selezionare una carta di credito")

        if self.payment_method_id.id == pp_journal.id and not self.pay_pal_tran_id:
        	raise ValidationError("Inserire un ID  transazione paypal")


        if  not isclose(self.amount_total,0.0) and self.payment_method_id.id == zero_journal.id :
        	raise ValidationError("Non è un ordine a costo zero!")


       	#self.action_confirm()
       	transient = None

       	if isclose(self.amount_total,0.0) or self.payment_method_id.id == zero_journal.id :
       		transient = self.env["netaddiction.zeropayment.executor"].create({})
       		transient.set_order_zero_payment(self)
       		
       	else:
       		if self.payment_method_id.id == cc_journal.id:
       			transient = self.env["netaddiction.positivity.executor"].create({})
       			transient._generate_invoice_payment(self.id,self.cc_selection.token)
       		if self.payment_method_id.id == pp_journal.id:
       			transient = self.env["netaddiction.paypal.executor"].create({})
       			transient._register_payment(self.partner_id.id, self.amount_total, self.id,self.pay_pal_tran_id)
       		if self.payment_method_id.id == contrassegno_journal.id:
       			transient = self.env["netaddiction.cod.register"].create({})
       			transient.set_order_cash_on_delivery(self.id)
       		if self.payment_method_id.id == cash_journal.id:
       			transient = self.env["netaddiction.cash.executor"].create({})
       			transient.register_cash_payment(self.partner_id.id, self.amount_total, self.id)

       	if transient:
       		transient.unlink()

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_id = fields.Many2one('account.payment', string='Pagamento', default=None)




       		 
