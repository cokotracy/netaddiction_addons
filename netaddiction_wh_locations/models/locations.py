# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

ERROR_BARCODE = "Barcode già esistente"
ERROR_NAME = "Nome già esistente"
ERROR_PRODUCT_LOCATION = "Un prodotto non può essere allocato due volte nello stesso ripiano"
ERROR_QTY_PLUS = "Non puoi allocare una quantità maggiore di quella del prodotto"
ERROR_QTY_MINUS = "Non puoi allocare una quantità minore di quella del prodotto"

class NetaddictionLocations(models.Model):
    _name = 'netaddiction.wh.locations'

    name = fields.Char(
        string="Nome",
        required="True")
    barcode = fields.Char(
        string="Barcode",
        size=10,
        required="True")
    wh_locations_line_ids = fields.One2many(
        comodel_name='netaddiction.wh.locations.line',
        inverse_name='wh_location_id',
        string='Allocazioni')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Azienda",
        required="True")
    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Magazzino",
        required="True")

    @api.multi
    @api.constrains('barcode','name','company_id','stock_location_id')
    def _check_barcode_name(self):
        """
        nomi uguali,barcode uguali
        """
        to_search=[
            ('id','!=',self.id),
            ('company_id','=',self.company_id.id),
            ('stock_location_id','=',self.stock_location_id.id),
            ('barcode','=',self.barcode)]
        #barcode
        get = self.search(to_search)
        if len(get)>0:
            raise ValidationError(ERROR_BARCODE)
        #name
        to_search=[
            ('id','!=',self.id),
            ('company_id','=',self.company_id.id),
            ('stock_location_id','=',self.stock_location_id.id),
            ('name','=',self.name)]
        get = self.search(to_search)
        if len(get)>0:
            raise ValidationError(ERROR_NAME)

class NetaddictionWhLocationsLine(models.Model):
    _name = 'netaddiction.wh.locations.line'

    wh_location_id = fields.Many2one(
        comodel_name='netaddiction.wh.locations',
        string="Ripiano",
        required="True"
        )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Prodotto",
        required="True"
        )
    qty = fields.Integer(
        'Quantità',
        required="True",
        default=1
        )

    @api.multi
    @api.constrains('product_id', 'wh_location_id')
    def _check_multi_pid_location(self):
        """
        Controlla che un prodotto non venga allocata due volte nello stesso ripiano
        """
        to_search = [
            ('id','!=',self.id),
            ('product_id','=',self.product_id.id),
            ('wh_location_id','=',self.wh_location_id.id)]
        get = self.search(to_search)
        if len(get)>0:
            raise ValidationError(ERROR_PRODUCT_LOCATIONS)

    #@api.multi
    #@api.constrains('qty','product_id')
    #def _check_max_qty(self):
    #    """
    #    controlla che la qty totale delle allocazioni di quel prodotto non sia maggiore della quantità
    #    del prodotto
    #    """
    #    qty_tot = self.product_id.qty_available
    #    to_search = [('product_id','=',self.product_id.id)]
    #    get = self.search(to_search)
    #    qty_now = 0
    #    for loc in get:
    #        qty_now = qty_now + loc.qty

    #    if qty_now > qty_tot:
    #        raise ValidationError(ERROR_QTY_PLUS)

    #    if qty_now < qty_tot:
    #        raise ValidationError(ERROR_QTY_MINUS)


class Products(models.Model):
    _inherit = 'product.product'

    product_wh_location_line_ids = fields.One2many(
        comodel_name='netaddiction.wh.locations.line',
        inverse_name='product_id',
        string='Allocazioni'
        )


class Products_template(models.Model):
    _inherit = 'product.template'

    product_wh_location_line_ids = fields.Boolean("Inverse")
