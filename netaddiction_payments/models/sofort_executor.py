# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
import payment_exception
import sofort
import cypher



class SofortExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con cc tramite bnl positivity, e per registrare carte di credito da BO in maniera sicura
    """
    _name = "netaddiction.sofort.executor"




    def initiate_payment(self,success_url, abort_url, default_url, loss_url, refund_url, order_name, amount):
        """

        Primo metodo da chiamare per effettuare un pagamento su Sofort
            Parametri:
            -amount: quantità da pagare, IMPORTANTE: COMPRESE SPESE DI SPEDIZIONE
            -success_url: url a cui reindirizzare l'utente in caso di successo nel pagamento sofort
            -abort_url: url a cui reindirizzare l'utente in caso di fallimento nel pagamento sofort
            -default_url: url su cui ricevere la risposta da sofort. deve essere tipo 'http://9f372dbc.ngrok.io/bnl.php?trn={0}' con parametro 'trn' che  inserisce il metodo e che sarà restituito da sofort all'url indicato
            -loss_url: url su cui ricevere la risposta da sofort. deve essere tipo 'http://9f372dbc.ngrok.io/bnl.php?trn={0}' con parametro 'trn' che  inserisce il metodo e che sarà restituito da sofort all'url indicato
            -refund_url: url su cui ricevere la risposta da sofort. deve essere tipo 'http://9f372dbc.ngrok.io/bnl.php?trn={0}' con parametro 'trn' che  inserisce il metodo e che sarà restituito da sofort all'url indicato
            -order_name: nome dell'ordine
            Returns:
            -se tutto ok: un dizionario con chiavi 
                'url' : url da tornare al cliente per pagare
                'transaction_id' : id della transazione sofort --> da controllare col valore tornato da sofort tramite POST
            -False altrimenti
            

        """

        encripted_username = self.env["ir.values"].search([("name","=","sofort_username")]).value
        encripted_apikey = self.env["ir.values"].search([("name","=","sofort_apikey")]).value
        encripted_project = self.env["ir.values"].search([("name","=","sofort_project")]).value
        
    
        key = self.env["ir.config_parameter"].search([("key","=","sofort.key")]).value

        username = cypher.decrypt(key,encripted_username)
        apikey = cypher.decrypt(key,encripted_apikey)
        project = cypher.decrypt(key,encripted_project)

        print "%s %s %s " %(username, apikey, project)
        client = sofort.Client(username, apikey, project,
            success_url = success_url,
            abort_url = abort_url,
            country_code='IT',
            notification_urls = {
                'default': default_url.format(sofort.TRANSACTION_ID),
                'loss': loss_url.format(sofort.TRANSACTION_ID),
                'refund': refund_url.format(sofort.TRANSACTION_ID),
            },
            reasons = ["acquisto su multiplayer.com: ordine %s" % order_name]
            )



        t= client.payment(amount)


        if t:
            return {
            'url':t.payment_url,
            'transaction_id' : t.transaction
            }
        else:
            return False




    def register_payment(self,user_id, amount, order_id,transaction_id):
        """
        metodo per registrare il pagamento sofort
        Parametri:
        -user_id: id dell'utente
        -amount: totale pagato nella transazione sofort
        -order_id: id dell'ordine
        -transaction_id: id transazione sofort
        Returns:
            -se tutto ok: True
            -altrimenti Raise PaymentException

        """
        print "HERE"
        pp_aj = self.env['ir.model.data'].get_object('netaddiction_payments', 'sofort_journal')
        pay_inbound = self.env["account.payment.method"].search([("payment_type","=","inbound")])
        pay_inbound = pay_inbound[0] if isinstance(pay_inbound,list) else pay_inbound
        if pp_aj and pay_inbound:
            name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
            pp_id = pp_aj.id
            order = self.env["sale.order"].search([("id","=",order_id)])
            payment = self.env["account.payment"].create({"partner_type" : "customer", "partner_id" : user_id, "journal_id" : pp_id, "amount" : amount, "order_id" : order_id, "state" : 'draft', "payment_type" : 'inbound', "payment_method_id" : pay_inbound.id, "name" : name, 'communication' : order.name, 'sofort_transaction_id': transaction_id,  })

            order.payment_method_id = pp_aj.id
            order.action_confirm()

            self._set_order_to_invoice(order)

            inv_lst = order.action_invoice_create()

            payment.invoice_ids = [(4, inv, None) for inv in inv_lst]

            for inv_id in inv_lst:
                inv = self.env["account.invoice"].search([("id","=",inv_id)])
                inv.signal_workflow('invoice_open')
                # inv.payement_id = [(6, 0, [payment.id])]

            payment.post()

            return True
        else:
            raise payment_exception.PaymentException(payment_exception.SOFORT,"impossibile trovare il metodo di pagamento Sofort")


    def _set_order_to_invoice(self,order):
        for line in order.order_line:
            line.qty_to_invoice = line.product_uom_qty







