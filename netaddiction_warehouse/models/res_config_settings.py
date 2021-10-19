from datetime import datetime

from odoo import fields, models
from odoo.exceptions import ValidationError


class Config(models.TransientModel):
    _inherit = 'res.config.settings'

    bartolini_prefix_file1 = fields.Char(
        string="Prefisso File1 Bartolini",
        config_parameter="bartolini_prefix_file1",
    )

    bartolini_prefix_file2 = fields.Char(
        string="Prefisso File2 Bartolini",
        config_parameter="bartolini_prefix_file2",
    )

    contrassegno_id = fields.Many2one(
        'account.journal',
        string="Metodo di pagamento per contrassegno",
        config_parameter="contrassegno_id",
    )

    hour_available = fields.Char(
        string="Ora oltre la quale la spedizione di prodotti presenti"
               " slitta a domani",
        config_parameter="hour_available",
    )

    hour_not_available = fields.Char(
        string="Ora oltre la quale la spedizione di prodotti non presenti"
               " slitta a domani",
        config_parameter="hour_not_available",
    )

    shipping_days = fields.Integer(
        string="Giorni di spedizione di default (può essere anche una media)",
        config_parameter="shipping_days",
    )
