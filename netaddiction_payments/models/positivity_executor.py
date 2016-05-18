# -*- coding: utf-8 -*-

from openerp import models, fields, api
from suds.client import Client
from openerp.exceptions import ValidationError
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

        return self.token_enroll(self.pan,self.month,self.year,self.customer.id,self.customer.email,self.name)




    def enroll_3DS(self,partner_id,partner_email,amount,card_holder,url,token):
        """Metodo che si interfaccia con BNL per iniziare una verifica 3dsecure
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La MPIEnrollResponse altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP
        """
    	client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/MPIGatewayPort?wsdl")
    	request_data = client.factory.create('MPIEnrollRequest')


        tid, kSig = self.get_tid_ksig()
        shop_id = partner_id
        shop_user_ref = partner_email

        currency = "EUR"

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
        

        if response.error:
            return False
        else:
            return response

 



    def token_enroll(self,pan,exp_month,exp_year,partner_id,partner_email,card_holder):
        """Metodo che si interfaccia con BNL per creare un token a partire dai dati di una carta.
            In caso di successo viene creato anche l'oggetto odoo che rappresenta i dati di una cc per un cliente
        Returns:
        - False se c'è un errore dalla risposta bnl
        - L'oggetto cc in odoo altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP
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
            return self.env["netaddiction.partner.ccdata"].create({'token':response.payInstrToken,'month': exp_month,'year': exp_year, 'name' : card_holder,'last_four': last_four,'customer_id': partner_id})
    
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


    def check_card(self,partner_id,partner_email,amount,token,enrStatus,authStatus,cavv,xid,order_id):
        """Metodo che si interfaccia con BNL per iniziare una verificare la autenticità e validità di una carta.
        In caso di successo viene creato il pagamento associato all'ordine (order_id).
        Richiede dei parametri ricevuti in dalla verifica del 3dsecure (enrStatus,authStatus,cavv,xid)
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La PaymentAuthResponse altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP
        """

        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")


        request_data = client.factory.create('PaymentAuthRequest')
        
        tid, kSig = self.get_tid_ksig()

        shop_id = partner_id
        shop_user_ref = partner_email
        token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])
        currency = "EUR"
        trType ="VERIFY"
        
        lst=[tid, shop_id,shop_user_ref,trType,amount,currency, token]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.shopUserRef = shop_user_ref
        request_data.signature =signature       
        request_data.payInstrToken = token
        request_data.trType = trType
        request_data.amount = amount
        request_data.currencyCode = currency
        request_data.enrStatus = enrStatus
        request_data.authStatus = authStatus
        request_data.cavv = cavv
        request_data.xid = xid

        response = client.service.auth(request_data)
        print response
        
        if response.error:
            return False
        else:
            cc_journal = self.env["account.journal"].search([("name","=","Carta di credito")]).id
            token_card = self.env["netaddiction.partner.ccdata"].search([("token","=",token)])
            self.env["account.payment"].create({'order_id':order_id, 'payment_type':'inbound', 'partner_type':'customer', 'partner_id':partner_id,'amount':amount,'journal_id':cc_journal,'payment_date':fields.Datetime.now(),'token':token,'last_four':token_card.last_four,'month':token_card.month,'year':token_card.year,'name':token_card.name,'cc_status':'init'})
            return response


    def auth(self,partner_id,partner_email,amount,token):
        #TODO cambiare lo stato del pagamento?
        """Metodo che si interfaccia con BNL per effettuare una autorizzazione di un pagamento.
        
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La PaymentAuthResponse altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP
        """

        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")


        request_data = client.factory.create('PaymentAuthRequest')
        
        tid, kSig = self.get_tid_ksig_MOTO()

        shop_id = partner_id
        shop_user_ref = partner_email
        token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])
        currency = "EUR"
        trType ="AUTH"
        
        lst=[tid, shop_id,shop_user_ref,trType,amount,currency, token]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.shopUserRef = shop_user_ref
        request_data.signature =signature       
        request_data.payInstrToken = token
        request_data.trType = trType
        request_data.amount = amount
        request_data.currencyCode = currency

        response = client.service.auth(request_data)
        print response
        
        if response.error:
            return False
        else:
            return response


 
    def confirm(self,partner_id,amount,refTranID):
        #TODO cambiare lo stato del pagamento?
        """Metodo che si interfaccia con BNL per effettuare una conferma di un pagamento.
        
        Returns:
        - False se c'è un errore dalla risposta bnl
        - La PaymentConfirmResponse altrimenti
        Throws:
        -Le eccezioni legate alle chiamate SOAP
        """

        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")


        request_data = client.factory.create('PaymentConfirmRequest')

        
        tid, kSig = self.get_tid_ksig_MOTO()

        shop_id = partner_id
        token = cypher.hmacmd5(kSig,[pan,exp_month,exp_year])

        
        lst=[tid, shop_id,amount,refTranID]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.signature =signature       
        request_data.amount = amount
        request_data.refTranID = refTranID


        response = client.service.auth(request_data)
        print response
        
        if response.error:
            return False
        else:
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




