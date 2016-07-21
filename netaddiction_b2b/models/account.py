# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Account(models.Model):
	_inherit = "account.invoice"

	shipping_address = fields.Many2one(string="Indirizzo di spedizione",comodel_name="res.partner")

	pick_id = fields.Many2one(string="Stock Picking per dati", comodel_name="stock.picking")