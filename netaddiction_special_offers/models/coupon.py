# Copyright 2020 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import ast
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CouponProgram(models.Model):
    _inherit = 'coupon.program'

    digital_bonus_id = fields.Many2one(
        'sale.coupon.program.digital.bonus',
        string="Digital Bonus",
        readonly=True
    )

    def create_digital_bonus(self, name):
        return self.env['sale.coupon.program.digital.bonus'].create({
                'name': name,
                'coupon_id': self.id
            })

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get('reward_type') == 'digital_bonus':
            digital_bonus = res.create_digital_bonus(vals['name'])
            res.digital_bonus_id = digital_bonus.id
        return res

    def write(self, vals):
        for item in self:
            if vals.get('reward_type') == 'digital_bonus':
                if item.digital_bonus_id:
                    item.self.digital_bonus_id.active = True
                else:
                    res = item.create_digital_bonus(item.name)
                    vals['digital_bonus_id'] = res.id
            elif vals.get('reward_type'):
                if item.digital_bonus_id:
                    item.digital_bonus_id.active = False
            super().write(vals)
        return True

    def update_products_ids(self):
        if self.rule_products_domain:
            if not self.discount_apply_on == "specific_products":
                raise UserError("Il campo 'Sconto applicato' non è impostato in 'Su prodotti specifici'")
            domain = ast.literal_eval(self.rule_products_domain)
            products = self.env["product.product"].sudo().search(domain)
            if not products:
                raise UserError("Nessun prodotto trovato per il seguente dominio")
            self.write({'discount_specific_product_ids': [(6, 0, [p.id for p in products])]})

    def cron_update_products_ids(self):
        for program in self.search([("active", "=", True), ("rule_date_from", "<=", datetime.now()), ("rule_date_to", ">=", datetime.now())]):
            try:
                program.update_products_ids()
            except Exception:
                _logger.error(f"Impossibile aggiornare i prodotti per il programma: {program.name}")

class SaleCouponReward(models.Model):
    _inherit = 'coupon.reward'

    reward_type = fields.Selection(
        selection_add=[('digital_bonus', 'Digital Bonus')],
        help="Discount - Reward will be provided as discount.\n" +
        "Free Product - Free product will be provide as reward \n" +
        "Free Shipping - Free shipping will be provided as reward (Need delivery module) \n" +
        "Digital Bonus - Free shipping of a Digital bonus"
     )

    def name_get(self):
        result = []
        reward_names = super().name_get()
        digital_bonus_reward_ids = self.filtered(
            lambda reward: reward.reward_type == 'digital_bonus'
        ).ids
        for res in reward_names:
            coupon = self.env['coupon.program'].browse(res[0])
            result.append((res[0], res[0] in digital_bonus_reward_ids
                          and _("Digital Bonus for coupon {}"
                          .format(coupon.name)) or res[1]))
        return result
