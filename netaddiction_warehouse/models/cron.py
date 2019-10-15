# -*- coding: utf-8 -*-
import datetime

from openerp import api, models


class Cron(models.Model):
    _name = 'netaddiction_warehouse.inventory_csv_builder'

    @api.model
    def run(self):
        domain = [['product_wh_location_line_ids', '!=', False], ['company_id', '=', 1]]
        inventory_file = self.env['stock.quant'].reports_inventario(domain, None)

        subject = 'Inventario mensile Multiplayer.com %s' % datetime.date.today()
        email_from = 'supporto@multiplayer.com'
        reply_to = 'matteo.piciucchi@netaddiction.it'
        email_to = "matteo.piciucchi@netaddiction.it,amministrazione@netaddiction.it"
        body = """
        """
        values = {
            'subject': subject,
            'body_html': '',
            'email_from': email_from,
            'email_to': email_to,
            'reply_to': reply_to,
        }
        email = self.env['mail.mail'].create(values)
        email['attachment_ids'] = [(6, 0, [inventory_file]), ]

        email.send()
