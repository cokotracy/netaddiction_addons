# -*- coding: utf-8 -*-

from openerp import models, fields, api
from suds.client import Client
from openerp.exceptions import ValidationError
from float_compare import isclose
import cypher




def compute_last_four(pan):
    str_pan = str(pan)
    return "".join([str_pan[:4],"XXXXXXXX",str_pan[12:]])

class PositivityExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con cc tramite bnl positivity, e per registrare carte di credito da BO in maniera sicura
    """
    _name = "netaddiction.positivity.executor"

    pan = fields.Char(string="Pan")
    month = fields.Integer(string='Mese')
    year =  fields.Integer(string='Anno')
    name = fields.Char(string='Titolare')
    customer = fields.Many2one(comodel_name='res.partner',string="Cliente")
    ctype = fields.Char(string='Tipo Carta')




    @api.multi
    def execute(self):
        """Override del metodo execute, usato solo per fornire nel BO la possibilità di 
        aggiungere una carta a un cliente"""

        if not self.pan or not self.month or not self.year or not self.name or not self.customer:
            raise ValidationError('completare tutti i campi')
        if self.month < 1 or self.month > 12:
            raise ValidationError("il mese deve essere compreso tra 1 e 12")
        if self.year > 2999 or self.year < 1000:
            raise ValidationError("Anno non valido")

        return self.token_enroll(self.pan,self.month,self.year,self.customer.id,self.customer.email,self.ctype,self.name)




    def enroll_3DS(self,partner_id,partner_email,card_holder,url,token):
        """Metodo che si interfaccia con BNL per iniziare una verifica 3dsecure
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La MPIEnrollResponse altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP


        esempio return corretto
        (MPIEnrollResponse){
            tid = "06817209"
            rc = "IGFS_000"
            error = False
            errorDesc = None
            signature = "M0FbKhbRthoUANT6+CAMpG/grjKdcDCTB5FFbFuEpaQ="
            shopID = "253"
            xid = "MDAxODI3OTY4NDgxMDUzMTM2MjI="
            enrStatus = "Y"
            paReq = "eNpVUslywjAM/RWGOzgLYRvFMxTDNAMJAdKFo8fxQNpsOE6Bfn1t1qKTniQ/SU+GaCc4J2vOasEx+Lyq6JY3kthtfizDTbRsBfO5OTNn/ny9v1grlPJ9SqakiSEcrfgeww8XVVLk2GwbbQvQDSo6wXY0lxgo2794Ae4Y2gBdIWRceATTZzNsxxkMLKcH6JKHnGYcB5NoRIg3jrxF0Fiv5oDOYWBFnUtxwnZfEd8A1CLFOynLaojQ4XBoZ3UqkzKlJy7arMgA6QJAjwnDWnuVIjwmMfbJ6Lggnr2INp2AbI8+efv1I9/yvzwXkK6AmEqOLcPsGl3baJjG0BgMnT6gcxxopifRiuh1LwBK3WN0zejE/wCoEwiesxMe9BTNHQE/lkXOVYWS9u5DzCuGLcdWDbUH6LHA+FULzqSSbkKm0/H3Z5guXVfLfg5qxkSJZHbNC6UGgPQzdL0ouv4E5T39kD+cCblX"
            md = "2I2AIFJAAAA54776PAIB_FFFFFFFFFFFFFFF035599257000+43810000000126MDAxODI3OTY4NDgxMDUzMTM2MjI=6B"
            acsURL = "https://testbnl.netsw.it/BNL_pareq"
            acsPage = "<html><!-- MPIIGFS4.0 --><head></head><body><form name="pareqform" action="https://testbnl.netsw.it/BNL_pareq" method="POST"><noscript><br><br><center><h1>Transazione 3D-Secure</h1><h3>Submit per continuare</h3><input type="submit" value="Submit"/></center></noscript><input type="hidden" name="PaReq" value="eNpVUslywjAM/RWGOzgLYRvFMxTDNAMJAdKFo8fxQNpsOE6Bfn1t1qKTniQ/SU+GaCc4J2vOasEx+Lyq6JY3kthtfizDTbRsBfO5OTNn/ny9v1grlPJ9SqakiSEcrfgeww8XVVLk2GwbbQvQDSo6wXY0lxgo2794Ae4Y2gBdIWRceATTZzNsxxkMLKcH6JKHnGYcB5NoRIg3jrxF0Fiv5oDOYWBFnUtxwnZfEd8A1CLFOynLaojQ4XBoZ3UqkzKlJy7arMgA6QJAjwnDWnuVIjwmMfbJ6Lggnr2INp2AbI8+efv1I9/yvzwXkK6AmEqOLcPsGl3baJjG0BgMnT6gcxxopifRiuh1LwBK3WN0zejE/wCoEwiesxMe9BTNHQE/lkXOVYWS9u5DzCuGLcdWDbUH6LHA+FULzqSSbkKm0/H3Z5guXVfLfg5qxkSJZHbNC6UGgPQzdL0ouv4E5T39kD+cCblX"/><input type="hidden" name="MD" value="2I2AIFJAAAA54776PAIB_FFFFFFFFFFFFFFF035599257000+43810000000126MDAxODI3OTY4NDgxMDUzMTM2MjI=6B"/><input type="hidden" name="TermUrl" value="http://localhost:8069/"/></form></body><SCRIPT language='javascript'>document.pareqform.submit();</SCRIPT></html>"
            }



        """
    	client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/MPIGatewayPort?wsdl")
    	request_data = client.factory.create('MPIEnrollRequest')


        tid, kSig = self.get_tid_ksig()
        shop_id = partner_id
        shop_user_ref = partner_email

        currency = "EUR"
        amount = 100

        lst=[tid, shop_id,shop_user_ref,amount,currency,token,url]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.shopUserRef = shop_user_ref
        request_data.signature =signature
        request_data.amount = amount
        request_data.currencyCode = currency
        request_data.payInstrToken = token
        request_data.termURL = url

    	

        response = client.service.enroll(request_data)
        print response

        if response.error:
            return False
        else:
            return response

 



    def token_enroll(self,pan,exp_month,exp_year,partner_id,partner_email,brand,card_holder):
        """Metodo che si interfaccia con BNL per creare un token a partire dai dati di una carta.
            In caso di successo viene creato anche l'oggetto odoo che rappresenta i dati di una cc per un cliente
            brand = brand della carta (mastercard etc)
        Returns:
        - False se c'è un errore dalla risposta bnl
        - L'oggetto cc in odoo altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP


        esempio risposta corretta
        (TokenizerEnrollResponse){
            tid = "06817209"
            rc = "IGFS_000"
            error = False
            errorDesc = None
            signature = "2wNwr6h3fwAZUI74fM8I5EMuEm7VHwz2jaPEWGJhzgE="
            shopID = "253"
            payInstrToken = "cc3deaaef4aff849c27c479e494ad8f5"
            }

        """
        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/TokenizerGatewayPort?wsdl")
        request_data = client.factory.create('TokenizerEnrollRequest')
        
        tid, kSig = self.get_tid_ksig()

        shop_id = partner_id
        shop_user_ref = partner_email
        token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])
        
        lst=[tid, shop_id,shop_user_ref,pan,exp_month,exp_year, token]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.shopUserRef = shop_user_ref
        request_data.signature =signature       
        request_data.pan = pan
        request_data.expireMonth =exp_month
        request_data.expireYear = exp_year
        request_data.payInstrToken = token
        request_data.regenPayInstrToken = True
        print request_data
        response = client.service.enroll(request_data)
        print response
        
        if response.error:
            return False
        else:
            last_four = compute_last_four(pan)
            return self.env["netaddiction.partner.ccdata"].create({'token':response.payInstrToken,'month': exp_month,'year': exp_year, 'name' : card_holder,'last_four': last_four,'customer_id': partner_id,'ctype':brand})
    
    def token_delete(self,partner_id,token):
        """Metodo che si interfaccia con BNL per cancellare un token
        Returns:
        - False se c'è un errore dalla risposta bnl
        - True altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP
        """
        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/TokenizerGatewayPort?wsdl")
        request_data = client.factory.create('TokenizerDeleteRequest')
        
        tid, kSig = self.get_tid_ksig()
        shop_id = partner_id
        
        lst=[tid, shop_id, token]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.signature =signature       
        request_data.payInstrToken = token

        response = client.service.delete(request_data)
        if response.error:
            return False
        else:
            return True


    @api.one
    def check_card(self,partner_id,token,paRes,md,order_id):
        """Metodo che si interfaccia con BNL per iniziare una verificare la autenticità e validità di una carta.
        In caso di successo viene creato il pagamento associato all'ordine (order_id).
        Richiede dei parametri ricevuti in dalla verifica del 3dsecure (paRes,md)
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La PaymentAuthResponse altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP


        esempio di risposta corretta

        (MPIAuthResponse){
            tid = "06817209"
            rc = "IGFS_000"
            error = False
            errorDesc = None
            signature = "SSBxBxzu0PmJVYuFVED5RSOOlH0xqIsbWbdOHXHRJEk="
            shopID = "253"
            xid = "MDAxODIxODAwNTMxMDUzMTQxNTA="
            authStatus = "Y"
            eci = "00"
            }



        """

        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/MPIGatewayPort?wsdl")


        request_data = client.factory.create('MPIAuthRequest')


        
        tid, kSig = self.get_tid_ksig()

        shop_id = partner_id
        #shop_user_ref = partner_email
        #token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])
        #currency = "EUR"
        #trType ="VERIFY"
        #amount = 100
        
        #lst=[tid, shop_id,shop_user_ref,trType,amount,currency, token]
        lst=[tid, shop_id,paRes,md]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        #request_data.shopUserRef = shop_user_ref
        request_data.signature =signature   
        request_data.paRes = paRes
        request_data.md = md    
        #request_data.payInstrToken = token
        #request_data.trType = trType
        #request_data.amount = amount
        #request_data.currencyCode = currency
        #request_data.enrStatus = enrStatus
        #request_data.authStatus = authStatus
        #request_data.cavv = cavv
        #request_data.xid = xid

        response = client.service.auth(request_data)
        print response
        
        if response.error:
            return False
        else:
            #FATTURE PAGAMENTI
            self._generate_invoice_payment(order_id,token)
            return response


    def auth(self,partner_id,partner_email,amount,token,order_id):
        """Metodo che si interfaccia con BNL per effettuare una autorizzazione di un pagamento.
        se l'operazione ha successo, viene cambiato lo stato status della cc in auth nel pagamento corrispondente nell'ordine di id = order_id. Se non viene trovato un pagamento corrispondente ne crea uno.
        
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La PaymentAuthResponse altrimenti
        Raise:
        - PaymentException se non c'è un pagamento associato all'ordine con l'amount indicato o s el'order id è sbagliato
        -Le eccezioni legate alle chiamate SOAP

        esempio di return se corretto

        (PaymentAuthResponse){
            tid = "06822153"
            rc = "IGFS_000"
            error = False
            errorDesc = "TRANSAZIONE OK"
            signature = "j/+cZbR8KrQX2CCDE4LUBDtHRu2qYmYdKM8vBN1LjvE="
            shopID = "253"
            tranID = 3062249430008421
            authCode = "856286"
            brand = "VISA"
            maskedPan = "455777******2229"
            payInstrToken = "cc3deaaef4aff849c27c479e494ad8f5"
            status = "C"
        }


        """

        (order, cc_journal) = self._check_payment(order_id,amount)

        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")


        request_data = client.factory.create('PaymentAuthRequest')
        print request_data
        
        tid, kSig = self.get_tid_ksig_MOTO()

        shop_id = partner_id
        shop_user_ref = partner_email
        #token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])
        currency = "EUR"
        trType ="AUTH"

        vc_amount = int(amount * 100 )
        
        lst=[tid, shop_id,shop_user_ref,trType,vc_amount,currency, token]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.shopUserRef = shop_user_ref
        request_data.signature =signature       
        request_data.payInstrToken = token
        request_data.trType = trType
        request_data.amount = vc_amount
        request_data.currencyCode = currency

        response = client.service.auth(request_data)
        print response
        
        if response.error:
            return False
        else:
            self._set_payment_or_create('auth',order,amount,response.tranID,token,cc_journal)                
            return response


 
    def confirm(self,partner_id,amount,refTranID,order_id,token):
        """Metodo che si interfaccia con BNL per effettuare una conferma di un pagamento.
        se l'operazione ha successo, viene cambiato lo stato status della cc in confirm nel pagamento corrispondente nell'ordine di id = order_id. Se non viene trovato un pagamento corrispondente ne crea uno.
        
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La PaymentConfirmResponse altrimenti
        Raise:
        - PaymentException se non c'è un pagamento associato all'ordine con l'amount indicato o s el'order id è sbagliato
        -Le eccezioni legate alle chiamate SOAP


        esempio di return se corretto
        (PaymentConfirmResponse){
            tid = "06822153"
            rc = "IGFS_000"
            error = False
            errorDesc = "TRANSAZIONE OK"
            signature = "warzxyGEgIwIBvfI7BhpdPE6MXxl9KG9XkqktvF1XwM="
            shopID = "253"
            tranID = 3062249590544417
            pendingAmount = 0
            }
        """

        (order, cc_journal) = self._check_payment(order_id,amount)

        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")


        request_data = client.factory.create('PaymentConfirmRequest')


        vc_amount = int(amount * 100 )
        
        tid, kSig = self.get_tid_ksig_MOTO()

        shop_id = partner_id
        #token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])

        
        lst=[tid, shop_id,vc_amount,refTranID]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.signature =signature       
        request_data.amount = vc_amount
        request_data.refTranID = refTranID
        request_data.splitTran = False
        #request_data.payInstrToken = token
        print request_data

        response = client.service.confirm(request_data)
        print response
        
        if response.error:
            return False
        else:
            self._set_payment_or_create('posted',order,amount,refTranID,token,cc_journal)
            return response


    def get_tid_ksig(self):
        """utility method
        """
        encripted_tid = self.env["ir.values"].search([("name","=","positivity_tid")]).value
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        encripted_kSig = self.env["ir.values"].search([("name","=","positivity_kSig")]).value
        kSig = cypher.decrypt(key,encripted_kSig)
        tid = cypher.decrypt(key,encripted_tid)
        return (tid, kSig)



    def get_tid_ksig_MOTO(self):
        """utility method
        """
        encripted_tid = self.env["ir.values"].search([("name","=","positivity_tid_MOTO")]).value
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        encripted_kSig = self.env["ir.values"].search([("name","=","positivity_kSig_MOTO")]).value
        kSig = cypher.decrypt(key,encripted_kSig)
        tid = cypher.decrypt(key,encripted_tid)
        return (tid, kSig)

    @api.one
    def _generate_invoice_payment(self,order_id,token):
        order = self.env["sale.order"].search([("id","=",order_id)])
        if order:
            if order.state == 'draft':
                order.action_confirm()

            if order.state == 'sale':
                cc_journal  = self.env['ir.model.data'].get_object('netaddiction_payments','cc_journal')
                token_card = self.env["netaddiction.partner.ccdata"].search([("token","=",token)])
                inv_lst = []

                for line in order.order_line:
                    #resetto la qty_to_invoice di tutte le linee
                    line.qty_to_invoice = 0
                for delivery in order.picking_ids:                    
                    for stock_move in delivery.move_lines_related:
                        self._set_order_to_invoice(stock_move,order)

                    self._set_delivery_to_invoice(delivery,order)

                    inv_lst += order.action_invoice_create()

                pay_inbound = self.env["account.payment.method"].search([("payment_type","=","inbound")])
                pay_inbound = pay_inbound[0] if isinstance(pay_inbound,list) else pay_inbound
                if cc_journal and pay_inbound:
                    cc_journal_id = cc_journal.id
                    order.payment_method_id = cc_journal_id
                    for inv in inv_lst:
                        name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
                        invoice = self.env['account.invoice'].search([("id","=",inv)])

                        if not isclose(order.amount_total,0.0):
                            #una spedizione potrebbe essere anche a costo zero, in quel caso non ci sono pagamenti
                            payment = self.env["account.payment"].create({"partner_type" : "customer", "partner_id" : order.partner_id.id, "journal_id" : cc_journal_id, "amount" : invoice.amount_total, "order_id" : order.id, "state" : 'draft', "payment_type" : 'inbound', "payment_method_id" : pay_inbound.id, "name" : name, 'communication' : order.name, 'cc_token':token,'cc_last_four':token_card.last_four,'cc_month':token_card.month,'cc_year':token_card.year,'cc_name':token_card.name,'cc_status':'init','cc_type':token_card.ctype })

                            payment.invoice_ids = [(4, inv, None) ]

                        invoice.signal_workflow('invoice_open')

    @api.one
    def _set_order_to_invoice(self,stock_move,order):
        """dato 'order' imposta qty_to_invoice alla quantità giusta solo per i prodotti che si trovano in 'stock_move'
        """
        prod_id = stock_move.product_id
        qty = stock_move.product_uom_qty

        lines = [line for line in order.order_line if line.product_id == prod_id ]
        for line in lines:
            qty_to_invoice = qty if qty < line.product_uom_qty else line.product_uom_qty

            line.qty_to_invoice += qty_to_invoice

            qty = qty - qty_to_invoice

            if qty <= 0:
                break

    @api.one
    def _set_delivery_to_invoice(self,pick,order):
        """dato 'order' imposta qty_to_invoice per una spedizione 
        """
        lines = [line for line in order.order_line if line.is_delivery and line.price_unit == pick.carrier_price and  line.qty_invoiced < line.product_uom_qty]

        if lines:
            lines[0].qty_to_invoice = 1



    @api.one
    def _set_payment_or_create(self,state,order,amount,tranID,token,cc_journal):

        found = False
        for payment in order.account_payment_ids:
            if (isclose(payment.amount,amount)) and payment.journal_id.id == cc_journal.id and not payment.state == 'posted':
                found = True
                payment.cc_tran_id = tranID
                if state == 'auth':
                    payment.cc_status = state
                elif state == 'posted':
                    payment.cc_status = 'commit'
                    payment.post()
                break
        if not found:
            #non ho trovato un pagamento da associare, ne creo uno (la situazione richiederà un intervento manuale)
            name = self.env['ir.sequence'].with_context(ir_sequence_date=fields.Date.context_today(self)).next_by_code('account.payment.customer.invoice')
            pay_inbound = self.env["account.payment.method"].search([("payment_type","=","inbound")])
            pay_inbound = pay_inbound[0] if isinstance(pay_inbound,list) else pay_inbound
            token_card = self.env["netaddiction.partner.ccdata"].search([("token","=",token)])
            payment = self.env["account.payment"].create({"partner_type" : "customer", "partner_id" : order.partner_id.id, "journal_id" : cc_journal.id, "amount" : amount, "order_id" : order.id, "state" : state, "payment_type" : 'inbound', "payment_method_id" : pay_inbound.id, "name" : name, 'communication' : ("PAGAMENTO SENZA FATTURA CREATO DURANTE %s CC" %state), 'token':token,'last_four':token_card.last_four,'month':token_card.month,'year':token_card.year,'name':token_card.name,'cc_status':'auth', 'cc_tran_id':tranID })

    @api.one
    def _check_payment(self,order_id,amount):
        order = self.env["sale.order"].search([("id","=",order_id)])
        cc_journal  = self.env['ir.model.data'].get_object('netaddiction_payments','cc_journal')
        found = False

        if not order:
            raise payment_exception.PaymentException(payment_exception.CREDITCARD,"impossibile trovare l'ordine %s"%order_id)

        for payment in order.account_payment_ids:
            if (isclose(payment.amount,amount)) and payment.journal_id.id == cc_journal.id and not payment.state == 'posted':
                found = True
                break
        if found:
            return (order, cc_journal)
        else:
            raise payment_exception.PaymentException(payment_exception.CREDITCARD,"nessun pagamento corrispondente a %s trovato nell'ordine %s"%(amount,order_id))







