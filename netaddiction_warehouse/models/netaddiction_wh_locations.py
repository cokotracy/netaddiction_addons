from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..tools.nawh_error import NAWHError


class StockLocation(models.Model):

    _inherit = 'stock.location'

    def unlink(self):
        return True


class NetaddictionLocations(models.Model):
    _name = 'netaddiction.wh.locations'
    _description = "Netaddiction WH Locations"
    _order = 'name'

    barcode = fields.Char(
        required=True,
        size=10,
        string="Barcode",
    )

    company_id = fields.Many2one(
        'res.company',
        required=True,
        string="Azienda",
    )

    name = fields.Char(
        required=True,
        string="Nome",
    )

    stock_location_id = fields.Many2one(
        'stock.location',
        required=True,
        string="Magazzino",
    )

    wh_locations_line_ids = fields.One2many(
        'netaddiction.wh.locations.line',
        'wh_location_id',
        string="Allocazioni",
    )

    @api.constrains('barcode', 'name', 'company_id', 'stock_location_id')
    def _check_barcode_name(self):
        """ nomi uguali, barcode uguali """
        for loc in self:
            dom = [
                ('company_id', '=', loc.company_id.id),
                ('stock_location_id', '=', loc.stock_location_id.id)
            ]

            # barcode
            if self.search_count(dom + [('barcode', '=', loc.barcode)]) > 1:
                raise ValidationError(
                    "Barcode '{}' già esistente!".format(loc.barcode)
                )

            # name
            if self.search_count(dom + [('name', '=', loc.name)]) > 1:
                raise ValidationError(
                    "Nome '{}' già esistente".format(loc.name)
                )

    @api.model
    def check_barcode(self, barcode):
        barcode = str(barcode).strip()
        res = self.search([('barcode', '=', barcode)])
        if not res:
            return NAWHError("Ripiano inesistente")
        return res
