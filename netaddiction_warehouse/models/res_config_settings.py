from datetime import datetime

from odoo import fields, models
from odoo.exceptions import ValidationError


class Config(models.TransientModel):
    _inherit = 'res.config.settings'

    bartolini_prefix_file1 = fields.Char(
        string="Prefisso File1 Bartolini",
    )

    bartolini_prefix_file2 = fields.Char(
        string="Prefisso File2 Bartolini",
    )

    contrassegno_id = fields.Many2one(
        'account.journal',
        string="Metodo di pagamento per contrassegno",
    )

    hour_available = fields.Char(
        string="Ora oltre la quale la spedizione di prodotti presenti"
               " slitta a domani",
    )

    hour_not_available = fields.Char(
        string="Ora oltre la quale la spedizione di prodotti non presenti"
               " slitta a domani",
    )

    shipping_days = fields.Integer(
        string="Giorni di spedizione di default (può essere anche una media)"
    )

    def get_values(self):
        values = dict(super().get_values() or [])
        getter = self.env['ir.config_parameter'].sudo().get_param
        values.update({
            'bartolini_prefix_file1': getter('bartolini_prefix_file1') or '',
            'bartolini_prefix_file2': getter('bartolini_prefix_file2') or '',
            'contrassegno_id': int(getter('contrassegno_id') or 0),
            'hour_available': getter('hour_available') or "16:00",
            'hour_not_available': getter('hour_not_available') or "14:00",
            'shipping_days': int(getter('shipping_days') or 0),
        })
        return values

    def set_values(self):
        if self.hour_available:
            try:
                datetime.strptime(self.hour_available, '%H:%M')
            except ValueError:
                raise ValidationError(
                    "Formato orario non valido. Usare il formato 'HH:MM'."
                )
        if self.hour_not_available:
            try:
                datetime.strptime(self.hour_not_available, '%H:%M')
            except ValueError:
                raise ValidationError(
                    "Formato orario non valido. Usare il formato 'HH:MM'."
                )
        res = super().set_values()
        setter = self.env['ir.config_parameter'].sudo().set_param
        setter('bartolini_prefix_file1', self.bartolini_prefix_file1)
        setter('bartolini_prefix_file2', self.bartolini_prefix_file2)
        setter('contrassegno_id', str(self.contrassegno_id or 0))
        setter('hour_available', self.hour_available)
        setter('hour_not_available', self.hour_not_available)
        setter('shipping_days', str(self.shipping_days or 0))
        return res
