# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class ProductStockNotification(models.Model):
    #Private Attributes
    _name = 'product.stock.notification'
    _description = "Product Stock Notification"

    # -------------------
    # Fields Declarations
    # -------------------
    product_id = fields.Many2one('product.product', string='Product')
    email = fields.Char(string='Email')
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], string='State', default='draft')

    def cron_product_stock_notification_check(self):
        """This method will call from cron and will notify subscriber if product gets back into the stock 
        """
        for record in self.search([('state', '=', 'draft')]):
            if record.product_id.qty_available > 0:
                try:
                    record._send_product_stock_notification()
                    record.state = 'sent'
                    self.env.cr.commit()
                except Exception as e:
                    _logger.error(e)
                    _logger.error("Sending stock notification failed - {}".format(record.email))
                    self.env.cr.rollback()

    def _send_product_stock_notification(self):
        """Send notification to registered email id"""
        template = self.env.ref('website_stock_notify.email_template_stock_notification', False)
        template.send_mail(res_id=self.id, force_send=False)
