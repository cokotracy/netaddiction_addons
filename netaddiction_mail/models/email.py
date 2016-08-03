# -*- coding: utf-8 -*-

from openerp import models


class EmailDispatcher(models.TransientModel):
    """Classe di utilità associata a un transient model per  inviare e-mail
    """
    _name = "netaddiction.email.dispatcher"

    def send_mail(self, body, subject, email_from, recipients, attachment_ids=None):
        """
        recipients: lista di stringhe contenenti le mail
        """

        email_to = ",".join([r.email for r in recipients])
        values = {
            'subject': subject,
            'body_html': body,
            'email_from': email_from,
            'email_to': email_to,

        }

        email = self.env['mail.mail'].create(values)
        if attachment_ids:
            email['attachment_ids'] = [(6, 0, attachment_ids), ]
        email.send()

    def get_users_from_group(self, id_group):
        group = self.env.ref(id_group)
        if group:
            return self.env["res.users"].search([("groups_id", "in", group.id)])
        else:
            return False
