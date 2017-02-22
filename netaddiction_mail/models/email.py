# -*- coding: utf-8 -*-

from openerp import models


class EmailDispatcher(models.TransientModel):
    """Classe di utilità associata a un transient model per  inviare e-mail
    """
    _name = "netaddiction.email.dispatcher"

    def send_mail(self, body, subject, email_from, recipients, attachment_ids=None, reply_to=None):
        """
        recipients: lista di partners
        """

        email_to = ",".join([r.email for r in recipients])
        values = {
            'subject': subject,
            'body_html': body,
            'email_from': email_from,
            'email_to': email_to,
        }
        if reply_to:
            values['reply_to'] = reply_to

        email = self.env['mail.mail'].create(values)

        if attachment_ids:
            email['attachment_ids'] = [(6, 0, attachment_ids), ]
        
        email.send()

    def send_mail_fixed_recipients(self, body, subject, email_from, recipients, attachment_ids=None, reply_to=None):
        """
        recipients:  stringa contenente le mail
        """
        values = {
            'subject': subject,
            'body_html': body,
            'email_from': email_from,
            'email_to': recipients,
        }
        if reply_to:
            values['reply_to'] = reply_to

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

    # rimosso perchè troppo lento, in  res partner _notify_by_email. 
    # def send_notification(self, body, subject, email_from, recipients, attachment_ids=None, reply_to=None):

    #     recipient_partners = []
    #     for recipient in recipients:
    #         recipient_partners.append((4, recipient.sudo().partner_id.id))
    #     self.env['mail.message'].sudo().create({
    #         'type': 'notification',
    #         # 'author_id': sender.sudo().partner_id.id,
    #         'partner_ids': recipient_partners,

    #         'subject': subject,
    #         'body': body,

    #         'subtype': 'mt_comment'
    #     })

