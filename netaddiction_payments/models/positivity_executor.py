# -*- coding: utf-8 -*-

from openerp import models, fields, api
from suds.client import Client
import cypher




def compute_last_four(pan):
    str_pan = str(pan)
    return "".join([str_pan[:4],"XXXXXXXX",str_pan[12:]])

class PositivityExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con cc tramite bnl positivity
    """
    _name = "netaddiction.positivity.executor"

    def enroll_3DS(self,partner_id,partner_email,amount,card_holder,url,token):
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

    	print request_data

        response = client.service.enroll(request_data)
        print response

        if response.error:
            return False
        else:
            return response

 



    def token_enroll(self,pan,exp_month,exp_year,partner_id,partner_email,card_holder):
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


    def check_card(self,partner_id,partner_email,amount,token):
        #TODO PARAMETRI MPI
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

        response = client.service.auth(request_data)
        print response
        
        if response.error:
            return False
        else:
            return response


    def auth(self,partner_id,partner_email,amount,token):
        #TODO PARAMETRI MPI
        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")


        request_data = client.factory.create('PaymentAuthRequest')
        
        tid, kSig = self.get_tid_ksig()

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


        #TODO confirm


    def get_tid_ksig(self):
        encripted_tid = self.env["ir.values"].search([("name","=","positivity_tid")]).value
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        encripted_kSig = self.env["ir.values"].search([("name","=","positivity_kSig")]).value
        kSig = cypher.decrypt(key,encripted_kSig)
        tid = cypher.decrypt(key,encripted_tid)
        return (tid, kSig)




