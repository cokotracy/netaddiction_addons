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




    def initiate_payment(self):
        encripted_username = self.env["ir.values"].search([("name","=","sofort_username")]).value
        encripted_apikey = self.env["ir.values"].search([("name","=","sofort_apikey")]).value
        encripted_project = self.env["ir.values"].search([("name","=","sofort_project")]).value
        
    
        key = self.env["ir.config_parameter"].search([("key","=","sofort.key")]).value

        username = cypher.decrypt(key,encripted_username)
        apikey = cypher.decrypt(key,encripted_apikey)
        project = cypher.decrypt(key,encripted_project)

        print "%s %s %s %s " % (username, apikey, project, sofort.TRANSACTION_ID)

        client = sofort.Client(username, apikey, project,
            success_url = 'http://www.multiplayer.it',
            abort_url = 'http://www.example.com',
            country_code='IT',
            notification_urls = {
                'default': 'http://9f372dbc.ngrok.io/bnl.php?trn={0}'.format(sofort.TRANSACTION_ID),
                'loss': 'http://9f372dbc.ngrok.io/bnl.php?trn={0}'.format(sofort.TRANSACTION_ID),
                'refund': 'http://9f372dbc.ngrok.io/bnl.php?trn={0}'.format(sofort.TRANSACTION_ID),
            },
            reasons = "hai comprato su m.com, bravo!"
            )

        print client

        t= client.payment(12.2)

        print t

        print t.transaction
        print t.payment_url







