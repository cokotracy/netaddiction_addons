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

        suppliers = self.env['res.partner'].search([
            ('parent_id', '=', False),
            ('supplier', '=', True),
            ('active', '=', True),
            ('send_report', '=', True),
            ])

        for sup in suppliers:

            monday_report = sup.generate_monday_report()

            #trova i contatti a cui inviare la roba
            recipients = []

            for contact in sup.child_ids:
                if contact.send_contact_report:
                    recipients.append(contact)

            if len(recipients) > 0:
                subject = 'Report Multiplayer.com - %s' % sup.name
                email_from = 'acquisti@multiplayer.com'
                reply_to = 'riccardo.ioni@netaddiction.it'

                email_to = ",".join([r.email for r in recipients])
                body = """

                """
                values = {
                    'subject': subject,
                    'body_html': '',
                    'email_from': email_from,
                    'email_to': email_to,
                    'reply_to': reply_to,
                    'author_id': self.env.user.partner_id.id,
                    'message_type': 'email',
                    }
                email = self.env['mail.mail'].create(values)
                attachment_ids = []
                for i in monday_report:
                    attachment_ids.append(i.id)
                email['attachment_ids'] = [(6, 0, attachment_ids), ]
                email.send()
