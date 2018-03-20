# -*- coding: utf-8 -*-
from openerp import models, fields


class ChannelPilotPartner(models.Model):
    _inherit = 'res.partner'

    from_channelpilot = fields.Boolean(string='Da ChannelPilot', default=False)