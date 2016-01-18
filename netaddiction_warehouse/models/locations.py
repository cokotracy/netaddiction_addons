# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

from error import Error

ERROR_BARCODE = "Barcode già esistente"
ERROR_NAME = "Nome già esistente"
ERROR_PRODUCT_LOCATION = "Un prodotto non può essere allocato due volte nello stesso ripiano"
ERROR_QTY_PLUS = "Non puoi allocare una quantità maggiore di quella del prodotto"
ERROR_QTY_MINUS = "Non puoi allocare una quantità minore di quella del prodotto"

class NetaddictionLocations(models.Model):
    _name = 'netaddiction.wh.locations'

    _order = 'name'

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

    @api.model
    def check_barcode(self,barcode):
        barcode = str(barcode).strip()
        res = self.search([('barcode','=',barcode)])
        if len(res)==0:
            err = Error()
            err.set_error_msg("Ripiano inesistente")
            return err

        return res

class NetaddictionWhLocationsLine(models.Model):
    _name = 'netaddiction.wh.locations.line'

    #ordino per la quantità in modo tale da terminare i ripiani
    #con meno oggetti 
    _order = 'qty'

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

    ######################
    #FUNZIONI PER RICERCA#
    ######################
   
    @api.model
    def get_products(self,barcode):
        result = self.search([('wh_location_id.barcode','=',barcode)])

        if len(result)==0:
            err = Error()
            err.set_error_msg("Non sono stati trovati prodotti per il barcode")
            return err

        return result

    ################
    #FUNZIONI VARIE#
    ################

    @api.one 
    def decrease(self,qta):
        """
        decrementa la quantità allocata di qta
        """
        diff = self.qty - qta

        if diff < 0:
            err = Error()
            err.set_error_msg("Non puoi scaricare una quantità maggiore di quella allocata")
            return err

        if diff == 0:
            self.unlink()
        else:
            self.write({'qty' : diff})

        return True
        # TODO: LOG

    @api.one 
    def increase(self,qta):
        """
        incrementa la quantità allocata di qta
        """
        
        self.write({'qty' : self.qty + qta})

        # TODO: LOG

    @api.model
    def allocate(self,product_id,qta,new_location_id):
        """
        alloca in new_location_id la qta di product_id
        """
        result = self.search([('product_id','=',product_id),('wh_location_id','=',new_location_id)])

        if len(result)>0:
            #è già presente una locazione con questo prodotto
            #incremento
            result.increase(qta)
        else:

            attr={
               'product_id' : product_id,
               'qty' : qta,
               'wh_location_id' : new_location_id
            }
            self.create(attr)


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
