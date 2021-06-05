from odoo import models, fields, api
import datetime


class WaveB2B(models.Model):
    _inherit = "stock.picking.batch"

    def close_b2b_batch(self, batch):
        this_batch = self.browse(int(batch))
        batch_date = this_batch.create_date
        invoice = 0
        for pick in this_batch.picking_ids:
            pick.do_validate_orders(pick.id)
            for invoice in pick.sale_id.invoice_ids:
                inv_date = invoice.create_date
                if inv_date.date() == batch_date.date():
                    invoice = invoice.id
        this_batch.done()

        return {'invoice': invoice}
