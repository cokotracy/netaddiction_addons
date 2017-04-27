# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm

class GrouponLocations(models.Model):
    _name = 'groupon.wh.locations'
    _inherit = 'netaddiction.wh.locations'

    wh_locations_line_ids = fields.One2many(
        comodel_name='groupon.wh.locations.line',
        inverse_name='wh_location_id',
        string='Allocazioni')

class GrouponWhLocationsLine(models.Model):
    _name = 'groupon.wh.locations.line'
    _inherit = 'netaddiction.wh.locations.line'

    wh_location_id = fields.Many2one(
        comodel_name='groupon.wh.locations',
        string="Ripiano",
        required="True"
    )

class GrouponProducts(models.Model):
    _inherit = 'product.product'

    groupon_wh_location_line_ids = fields.One2many(
        comodel_name='groupon.wh.locations.line',
        inverse_name='product_id',
        string='Allocazioni Groupon')

class GrouponReserve(models.TransientModel):

    _name = "groupon.reserve.product"

    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    qty_available = fields.Integer(string="Qtà in magazzino")
    qty_to_reserve = fields.Integer(string="Quantità da riservare")

    @api.onchange('product_id')
    def _get_products_data(self):
        self.qty_available = self.product_id.qty_available

    @api.model
    def create(self, values):
        product_id = values['product_id']
        qty_to_reserve = values['qty_to_reserve']
        product = self.env['product.product'].browse(product_id)

        groupon_warehouse = self.env.ref('netaddiction_groupon.netaddiction_stock_groupon').id

        if qty_to_reserve > product.qty_available:
            raise except_orm('Errore grave', 'La quantità da riservare non può essere maggiore di quella disponibile')

        if qty_to_reserve < 0:
            raise except_orm('Errore gravissimo', 'Dai, serio, mi stai prendendo per i fondelli. Come pretendi di spostare una quantità negativa?')

        # trova le locations da cui spostare
        # crea le nuove location di groupon
        # decrementa le quantità
        locations = {}
        for location in product.product_wh_location_line_ids:
            if qty_to_reserve <= location.qty:
                locations[location] = qty_to_reserve
            else:
                locations[location] = location.qty
                qty_to_reserve -= location.qty

        for location in locations:
            # location.decrease(locations[location])
            # cerca se esiste la locazione speculare per il magazzino Groupon
            groupon_location = self.env['groupon.wh.locations'].search([('barcode', '=', location.wh_location_id.barcode)])
            if len(groupon_location) == 0:
                attr = {
                    'name': 'GRP%s' % (location.wh_location_id.name.replace('TR', ''),),
                    'barcode': location.wh_location_id.barcode,
                    'company_id': location.wh_location_id.company_id.id,
                    'stock_location_id': groupon_warehouse
                }
                groupon_new_location = self.env['groupon.wh.locations'].create(attr)
                print groupon_new_location
            print groupon_location
            # self.env['groupon.wh.locations.line'].allocate(product_id, locations[location], new_loc_id)
        # sposta il prodotto

        # controlla i limiti del prodotto

        return self
