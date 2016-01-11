# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api

class Discount(models.Model):
    """
    Settings per i tipi di sconti ammessi nell'Ordine
    """

    _name="netaddiction.order.discount"

    name=fields.Char(string="Tipo nome")

    res_model = fields.Char(string="Modello Riferimento", help="""inserire il nome esatto del modello di riferimento, vuoto se non 
        fa riferimento a nessun modello.""")


class OrdersDiscountline(models.Model):
    """
    Righe di sconto nell'ordine
    """

    _name = "netaddiction.order.discount.line"

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Ordine", required=True)

    type_id = fields.Many2one(
        comodel_name='netaddiction.order.discount',
        string="Tipo Sconto", required=True)

    value = fields.Float(string="Valore",default=0)

class OrdersOrderLine(models.Model):
    _inherit = 'sale.order'

    discount_lines = fields.One2many(comodel_name="netaddiction.order.discount.line",
        inverse_name="order_id", string="Sconti")

    discount_total = fields.Float(string="Sconto totale", compute="_compute_discount")

    @api.depends('discount_lines')
    def _compute_total_gift(self):
        for record in self:
            for discount in record.discount_lines:
                record.discount_total += discount.value