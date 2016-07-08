# -*- coding: utf-8 -*-

import csv

from datetime import date
from io import BytesIO

from openerp import api, models


class Cron(models.Model):
    _name = 'netaddiction.generate_and_send_monday_report'

    @api.model
    def run(self):
        """
        Questo cron richiama le funzioni crete per res.partner
        per generare i file di report e slow moving del lunedì
        e manda la mail ad ogni fornitore.
        """

        suppliers = self.env['res.partner'].search([('parent_id','=',False),('supplier','=',True),('send_report','=',True)])
        
        for sup in suppliers:
            monday_report = sup.generate_monday_report()
            slow_moving = sup.generate_slow_moving()

            #trova i contatti a cui inviare la roba
            contacts_ids = []

            for contact in sup.child_ids:
                if contact.send_contact_report:
                    contacts_ids.append(contact.id)

            print sup.name 
            print contacts_ids
            print '*'*10

            #TODO: MAIL