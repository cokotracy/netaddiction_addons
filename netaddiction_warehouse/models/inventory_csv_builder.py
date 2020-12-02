from datetime import date

from odoo import api, models


class InventoryCsvBuilder(models.AbstractModel):
    """ Abstract model: only runs a method within a cron """
    _name = 'netaddiction_warehouse.inventory_csv_builder'
    _description = "Netaddiction CSV Builder"

    @api.model
    def run(self):
        domain = [
            ('product_wh_location_line_ids', '!=', False),
            ('company_id', '=', 1),
        ]
        file_id = self.env['stock.quant'].reports_inventario(domain, None)

        email = self.env['mail.mail'].create({
            'attachment_ids': [(6, 0, [file_id])],
            'subject': 'Inventario mensile Multiplayer.com %s' % date.today(),
            'body_html': '',
            'email_from': 'supporto@multiplayer.com',
            'email_to': "matteo.piciucchi@netaddiction.it,"
                        "amministrazione@netaddiction.it",
            'reply_to': 'matteo.piciucchi@netaddiction.it',
        })
        email.send()
