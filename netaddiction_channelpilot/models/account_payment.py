# -*- coding: utf-8 -*-
from openerp import models, fields


class AccountPaymentChannelPilot(models.Model):
    """docstring for AccountPayment"""
    _inherit = 'account.payment'

    cp_typeID = fields.Char(string='Id ChannelPilot')
    cp_typeTitle = fields.Char(string='Tipo ChannelPilot')
    cp_original_date = fields.Char(string='Data pagamento su ChannelPilot')
