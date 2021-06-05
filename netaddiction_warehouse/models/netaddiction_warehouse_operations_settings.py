from odoo import fields, models


class NaWhOpSettings(models.Model):
    _name = 'netaddiction.warehouse.operations.settings'
    _description = "Netaddiction WH Operations Settings"

    company_id = fields.Many2one(
        'res.company',
        ondelete="restrict",
        required=True,
        string="Azienda",
    )

    operation = fields.Many2one(
        'stock.picking.type',
        ondelete="restrict",
        string="Operazione di Magazzino",
    )

    netaddiction_op_type = fields.Selection(
        [('reverse_scrape', "Reso Difettati"),
         ('reverse_resale', "Reso Rivendibile"),
         ('reverse_supplier', "Reso a Fornitore"),
         ('reverse_supplier_scraped', "Reso a Fornitore Difettati")],
        string="Tipo di Operazione",
    )
