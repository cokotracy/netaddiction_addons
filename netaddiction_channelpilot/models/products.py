# -*- coding: utf-8 -*-
from openerp import api, fields, models

class Template(models.Model):
    _inherit = 'product.product'

    channelpilot = fields.Boolean('ChannelPilot', default=False)
    channelpilot_blacklist = fields.Boolean('CP Blacklist', default=False)

    @api.multi
    def toggle_cp(self):
        for prod in self:
            prod.channelpilot = not prod.channelpilot
        return True

    @api.multi
    def toggle_cp_blacklist(self):
        for prod in self:
            prod.channelpilot_blacklist = not prod.channelpilot_blacklist
            prod.channelpilot = False if prod.channelpilot_blacklist else True
        return True
