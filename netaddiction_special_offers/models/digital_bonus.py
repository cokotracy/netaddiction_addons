# Copyright 2020 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import csv
import io

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class SaleCouponProgramDigitalBonus(models.Model):
    _name = 'sale.coupon.program.digital.bonus'
    _description = 'Digital Bonuses'

    name = fields.Char(
        string='Titolo',
        required=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    coupon_id = fields.Many2one(
        'coupon.program',
        string="Coupon",
        readonly=True,
    )

    filename = fields.Char(
        string="Filename"
    )

    csv_file = fields.Binary(
        string='File'
    )

    digital_bonus_code_ids = fields.One2many(
        'sale.coupon.program.digital.bonus.code',
        'digital_bonus_id',
        string='Codes List'
    )

    bonus_text = fields.Text(
        string="Bonus Text"
    )

    mail_body = fields.Text(
        string="Mail Body"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    qty_limit = fields.Integer(
        string="Quantità limite",
        default=0,
        help="Quantity zero means unlimited amount"
    )

    qty_sold = fields.Integer(
        string="Quantità venduta",
        default=0
    )

    @api.constrains('qty_limit', 'qty_sold')
    def check_limit(self):
        # TODO This metod is untested
        if self.qty_limit and self.qty_sold >= self.qty_limit:
            self.active = False

    def load_data_from_file(self):
        decoded64 = base64.b64decode(self.csv_file)
        decodedIO = io.StringIO(decoded64.decode())
        reader = csv.reader(decodedIO)

        bonus_code_obj = self.env["sale.coupon.program.digital.bonus.code"]

        for line in reader:
            if not bonus_code_obj.search([
                    ("digital_bonus_id", "=", self.id),
                    ("name", "=", line[0])
                    ]):
                bonus_code_obj.create({
                    'name': line[0],
                    'digital_bonus_id': self.id,
                })

    def assign_old_sale_orders(self):
        for item in self.filtered(lambda x: x.active):
            products = self.env['product.product'].search(
                safe_eval(item.coupon_id.rule_products_domain)
            )
            codes = [code for code in item.digital_bonus_code_ids
                     if not code.sent and not code.sale_order_id]
            if not codes:
                continue

            orders = self.env["sale.order"].search(
                [("order_line.product_id", "in", products.ids),
                 ("state", "in", ("sale", "problem", "partial_done", "done"))],
                order="date_order")
            for order in orders:
                codes_in_order = [code for code in order.digital_bonus_code_ids
                                  if code.digital_bonus_id.id == item.id]
                if codes_in_order:
                    continue
                order_lines = [ol for ol in order.order_line
                               if ol.product_id.id in products.ids]
                for ol in order_lines:
                    counter = 0
                    while counter < ol.product_uom_qty and codes:
                        code = codes.pop(0)
                        code.sale_order_id = order.id
                        code.sale_order_line_id = ol.id
                        counter += 1
                        # commentata perchè raddoppia la quantità
                        # item.qty_sold += 1

    def send_all_valid(self):
        codes = self.env["sale.coupon.program.digital.bonus.code"].search(
            [("digital_bonus_id", "=", self.id),
             ("sale_order_id", "!=", False),
             ("sale_order_line_id", "!=", False), ("sent", "=", False)]
        )
        codes = codes.filtered(lambda c: c.sale_order_line_id.qty_delivered
                               == c.sale_order_line_id.product_uom_qty)
        codes.send_code()

    def send_all_possible(self):
        codes = self.env["sale.coupon.program.digital.bonus.code"].search(
            [("digital_bonus_id", "=", self.id),
             ("sale_order_id", "!=", False),
             ("sale_order_line_id", "!=", False),
             ("sent", "=", False)]
        )
        codes.send_code()


class SaleCouponProgramDigitalBonusCode(models.Model):
    _name = 'sale.coupon.program.digital.bonus.code'
    _inherit = 'mail.thread'
    _description = 'Digital Bonus Code'

    name = fields.Char(
        string='Code',
        required=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Attached Order',
    )

    digital_bonus_id = fields.Many2one(
        'sale.coupon.program.digital.bonus',
        string='Attached Digital Bonus',
    )

    sent = fields.Boolean(
        string="Sent",
    )

    date_sent = fields.Datetime(
        string='Email sent date'
    )

    sent_by = fields.Many2one(
        'res.users',
        string='Sent by'
    )

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Attached sale Order Line',
    )

    def send_code(self):
        mail_template = self.env.ref(
            'netaddiction_special_offers.digital_bonus_mail_template'
        )

        for item in self.filtered(lambda i: i.sale_order_id):
            mail_template.send_mail(res_id=item.id, raise_exception=True)
            item.sent = True
            item.date_sent = fields.Datetime.now()
            item.sent_by = self.env.user.id
            item.message_change_thread(item.sale_order_id)

        return True
