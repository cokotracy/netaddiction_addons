# -*- coding: utf-8 -*-

from openerp import models, fields, api
from suds.client import Client
import cypher






class PositivityExecutor(models.TransientModel):
    """Classe di utilità associata a un transient model per effettuare e registrare
    pagamenti con cc tramite bnl positivity
    """
    _name = "netaddiction.positivity.executor"

    def enroll_3DS(self):
    	client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/MPIGatewayPort?wsdl")
    	request_data = client.factory.create('MPIEnrollRequest')
        encripted_tid = self.env["ir.values"].search([("name","=","positivity_tid")]).value
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        encripted_kSig = self.env["ir.values"].search([("name","=","positivity_kSig")]).value

        kSig = cypher.decrypt(key,encripted_kSig)


        tid = cypher.decrypt(key,encripted_tid)
        shop_id = 11223
        shop_user_ref = "lollo"
        amount = 5430
        currency = "EUR"
        pan = 4557772222222229
        exp_month = 12
        exp_year = 2016
        url = "https://pftest.bnlpositivity.it/service/"
        lst=[tid, shop_id,shop_user_ref,amount,currency,pan,exp_month,exp_year,url]
        signature = cypher.hmacsha256(kSig ,lst)

        request_data.tid = tid
        request_data.shopID = shop_id
        request_data.shopUserRef = shop_user_ref
        request_data.signature =signature
        request_data.amount = amount
        request_data.currencyCode = currency

        request_data.pan = pan
        request_data.expireMonth =exp_month
        request_data.expireYear = exp_year
        request_data.termURL = url

    	print request_data

        response = client.service.enroll(request_data)
        print response

        if response.error:
            return False
        else:
            return response

 



    def token_enroll(self):
        client = Client("https://s2stest.bnlpositivity.it/BNL_CG_SERVICES/services/PaymentTranGatewayPort?wsdl")
        request_data = client.factory.create('Token')
        encripted_tid = self.env["ir.values"].search([("name","=","positivity_tid")]).value
        key = self.env["ir.config_parameter"].search([("key","=","positivity.key")]).value
        encripted_kSig = self.env["ir.values"].search([("name","=","positivity_kSig")]).value

        kSig = cypher.decrypt(key,encripted_kSig)
        tid = cypher.decrypt(key,encripted_tid)

