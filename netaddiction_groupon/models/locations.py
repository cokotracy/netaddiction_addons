# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import Warning
import datetime

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

class GrouponReserve(models.Model):

    _name = "groupon.reserve.product"

    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    qty_available = fields.Integer(string="Qtà disponibile")
    qty_to_reserve = fields.Integer(string="Quantità da riservare")
    groupon_price = fields.Float(string="Prezzo di vendita a Groupon")
    name = fields.Text(string="Nome", compute="get_name")

    @api.one
    def get_name(self):
        self.name = self.product_id.display_name

    @api.onchange('product_id')
    def _get_products_data(self):
        self.qty_available = self.product_id.qty_available_now

    @api.model
    def create(self, values):
        product_id = values['product_id']
        qty_to_reserve = values['qty_to_reserve']
        groupon_price = values['groupon_price']

        if not product_id:
            raise Warning('Non hai scelto il prodotto da riservare')

        product = self.env['product.product'].browse(product_id)

        groupon_warehouse = self.env.ref('netaddiction_groupon.netaddiction_stock_groupon').id

        if qty_to_reserve > product.qty_available_now:
            raise Warning('La quantità da riservare non può essere maggiore di quella disponibile')

        if qty_to_reserve <= 0:
            raise Warning('Dai, serio, mi stai prendendo per i fondelli. Come pretendi di spostare una quantità negativa?')

        if groupon_price <= 0:
            raise Warning("Non hai assegnato un prezzo di vendita a Groupon")

        # trova le locations da cui spostare
        # crea le nuove location di groupon
        # decrementa le quantità
        locations = {}
        for location in product.product_wh_location_line_ids:
            if qty_to_reserve > 0:
                if qty_to_reserve <= location.qty:
                    locations[location] = qty_to_reserve
                    qty_to_reserve = 0
                else:
                    locations[location] = location.qty
                    qty_to_reserve -= location.qty

        for location in locations:
            location.decrease(locations[location])
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
                new_loc_id = groupon_new_location.id
            else:
                new_loc_id = groupon_location.id

            self.env['groupon.wh.locations.line'].allocate(product_id, locations[location], new_loc_id)

        # sposta il prodotto
        type_groupon_out = self.env.ref('netaddiction_groupon.groupon_type_out').id
        wh_stock = self.env.ref('stock.stock_location_stock').id
        attr = {
            'picking_type_id': type_groupon_out,
            'move_type': 'one',
            'priority': '1',
            'location_id': wh_stock,
            'location_dest_id': groupon_warehouse,
            'move_lines': [(0, 0, {'product_id': product_id, 'product_uom_qty': int(values['qty_to_reserve']),
                'state': 'draft',
                'product_uom': product.uom_id.id,
                'name': 'WH/Stock > Magazzino Groupon',
                'picking_type_id': type_groupon_out,
                'origin': 'Groupon %s' % (datetime.date.today(),)})],
        }
        pick = self.env['stock.picking'].sudo().create(attr)
        pick.sudo().action_confirm()
        pick.sudo().force_assign()
        for line in pick.pack_operation_product_ids:
            line.sudo().write({'qty_done': line.product_qty})
        pick.sudo().do_transfer()

        # controlla i limiti del prodotto
        product.do_action_quantity()

        return super(GrouponReserve, self).create(values)

class GrouponReturn(models.Model):

    _name = "groupon.return.product"

    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    qty_groupon = fields.Integer(string="Qtà groupon")
    qty_to_return = fields.Integer(string="Quantità da ritornare")
    name = fields.Text(string="Nome", compute="get_name")

    @api.one
    def get_name(self):
        self.name = self.product_id.display_name

    @api.onchange('product_id')
    def _get_products_data(self):
        self.qty_groupon = self.get_groupon_qty(self.product_id.id)

    @api.model
    def get_groupon_qty(self, product_id):
        groupon_warehouse = self.env.ref('netaddiction_groupon.netaddiction_stock_groupon').id
        results = self.env['stock.quant'].search([('product_id', '=', product_id), ('location_id', '=', groupon_warehouse)])
        qty = 0
        for res in results:
            qty += res.qty
        return qty

    @api.model
    def create(self, values):
        product_id = values['product_id']
        qty_to_return = values['qty_to_return']
        qty_groupon = int(self.get_groupon_qty(product_id))

        if not product_id:
            raise Warning('Non hai scelto il prodotto da ritornare')

        if qty_to_return > qty_groupon:
            raise Warning('La quantità da ritornae non può essere maggiore di quella disponibile nel magazzino Groupon')

        if qty_to_return <= 0:
            raise Warning('Dai, serio, mi stai prendendo per i fondelli. Come pretendi di spostare una quantità negativa?')

        product = self.env['product.product'].browse(product_id)

        # vedo le locazioni groupon e decremento
        locations = {}
        for location in product.groupon_wh_location_line_ids:
            if qty_to_return > 0:
                if qty_to_return <= location.qty:
                    locations[location] = qty_to_return
                    qty_to_return = 0
                else:
                    locations[location] = location.qty
                    qty_to_return -= location.qty

        # riporto nelle locazioni speculari del magazzino fisico
        for location in locations:
            location.decrease(locations[location])
            wh_location = self.env['netaddiction.wh.locations'].search([('barcode', '=', location.wh_location_id.barcode)])
            if wh_location:
                self.env['netaddiction.wh.locations.line'].allocate(product_id, locations[location], wh_location.id)

        # stock.picking in rientro
        type_groupon_in = self.env.ref('netaddiction_groupon.groupon_type_in').id
        wh_stock = self.env.ref('stock.stock_location_stock').id
        groupon_warehouse = self.env.ref('netaddiction_groupon.netaddiction_stock_groupon').id
        attr = {
            'picking_type_id': type_groupon_in,
            'move_type': 'one',
            'priority': '1',
            'location_id': groupon_warehouse,
            'location_dest_id': wh_stock,
            'move_lines': [(0, 0, {'product_id': product_id, 'product_uom_qty': int(values['qty_to_return']),
                'state': 'draft',
                'product_uom': product.uom_id.id,
                'name': 'Magazzino Groupon > WH/Stock',
                'picking_type_id': type_groupon_in,
                'origin': 'Groupon %s' % (datetime.date.today(),)})],
        }
        pick = self.env['stock.picking'].sudo().create(attr)
        pick.sudo().action_confirm()
        pick.sudo().force_assign()
        for line in pick.pack_operation_product_ids:
            line.sudo().write({'qty_done': line.product_qty})
        pick.sudo().do_transfer()

        # controlla i limiti del prodotto
        product.do_action_quantity()

        return super(GrouponReturn, self).create(values)
