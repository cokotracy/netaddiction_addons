# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
import datetime
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

    @api.model
    def get_products(self,barcode):
        """
        dato il barcode di un ripiano ritorna i prodotti allocati
        """
        result = self.search([('wh_location_id.barcode','=',barcode)])

        if len(result)==0:
            err = Error()
            err.set_error_msg("Non sono stati trovati prodotti per il barcode")
            return err

        return result

    ########################
    #INVENTORY APP FUNCTION#
    #ritorna un dict simile#
    #ad un json per il web #
    ########################
    @api.model
    def get_json_products(self, barcode):
        """
        ritorna un json con i dati per la ricerca per ripiano
        """
        is_shelf = self.env['netaddiction.wh.locations'].check_barcode(barcode)
        
        if isinstance(is_shelf,Error):
            return {'result' : 0, 'error' : is_shelf.get_error_msg()}

        results = self.get_products(barcode)

        if isinstance(results,Error):
            return {'result' : 0, 'error' : results.get_error_msg()}

        allocations = {
            'result' : 1,
            'shelf' : is_shelf.name,
            'barcode' : barcode,
            'products' : []
        }

        for res in results:
            allocations['products'].append({
                'product_name' : res.product_id.display_name,
                'qty' : res.qty,
                'barcode' : res.product_id.barcode
                })

        return allocations

    @api.model
    def put_json_new_allocation(self, barcode, qty, product_id, now_wh_line):
        """
        sposta la quantità qty dal ripiano barcode al new_shelf
        """
        is_shelf = self.env['netaddiction.wh.locations'].check_barcode(barcode)
        
        if isinstance(is_shelf,Error):
            return {'result' : 0, 'error' : is_shelf.get_error_msg()}

        new_shelf = is_shelf.id

        this_line = self.search([('id','=',int(now_wh_line)),('product_id','=',int(product_id))])

        if len(this_line) == 0:
            return {'result' : 0, 'error' : 'Prodotto non più presente in questa locazione'}

        if(this_line.wh_location_id.id == new_shelf):
            return {'result' : 0, 'error' : 'Non puoi spostare un prodotto nella stessa locazione di partenza'}

        dec = this_line.decrease(qty)
        if isinstance(dec,Error):
            return {'result' : 0, 'error' : dec.get_error_msg()}
        
        self.allocate(product_id,qty,new_shelf)

        product = self.env['product.product'].search([('id','=',int(product_id))])
        

        return {'result' : 1, 'product_barcode' :product.barcode }

        
    ############################
    #END INVENTORY APP FUNCTION#
    ############################

    ################
    #FUNZIONI VARIE#
    ################

    @api.one 
    def decrease(self,qta):
        """
        decrementa la quantità allocata di qta
        """
        diff = self.qty - int(qta)

        if diff < 0:
            err = Error()
            err.set_error_msg("Non puoi scaricare una quantità maggiore di quella allocata")
            return err

        if diff == 0:
            self.unlink()
        else:
            self.write({'qty' : diff})

        return True

    @api.one 
    def increase(self,qta):
        """
        incrementa la quantità allocata di qta
        """
        self.write({'qty' : self.qty + int(qta)})


    @api.model
    def allocate(self,product_id,qta,new_location_id):
        """
        alloca in new_location_id la qta di product_id
        """
        result = self.search([('product_id','=',int(product_id)),('wh_location_id','=',int(new_location_id))])
        
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

class ProductsMovement(models.TransientModel):

    _name = "netaddiction.products.movement"

    barcode = fields.Char(string="Barcode")
    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    qty_available = fields.Integer(string="Qtà in magazzino")
    allocation = fields.Text(string="Allocazioni")
    qty_to_move = fields.Integer(string="Quantità da muovere o riallocare")
    new_allocation = fields.Many2one(string="Dove Allocare/Scaricare", comodel_name="netaddiction.wh.locations")

    action = fields.Selection(selection=(
        ('scraped', 'Difettato'),
        ('rialloca', 'Rialloca')), string="Azione", required=True)

    @api.onchange('barcode')
    def _get_product_from_barcode(self):
        result = self.env['product.product'].search([('barcode','=',self.barcode)])
        if len(result) > 0:
            self.product_id = result[0].id
            self.qty_available = self.product_id.qty_available
            text = ''
            for line in self.product_id.product_wh_location_line_ids:
                text += str(line.qty) + ' in ' + str(line.wh_location_id.name) +'\n'
            self.allocation = text

    @api.onchange('product_id')
    def _get_products_data(self):
        self.barcode = self.product_id.barcode
        self.qty_available = self.product_id.qty_available
        text = ''
        for line in self.product_id.product_wh_location_line_ids:
            text += str(line.qty) + ' in ' + str(line.wh_location_id.name) +'\n'
        self.allocation = text

    @api.one 
    def execute(self):
        if not self.product_id:
            raise ValidationError("Devi scegliere un prodotto")

        if self.action == 'rialloca':
            if self.qty_to_move > 0 and self.new_allocation:
                self.env['netaddiction.wh.locations.line'].allocate(self.product_id.id,self.qty_to_move,self.new_allocation.id)
                self.qty_available = self.product_id.qty_available
                text = ''
                for line in self.product_id.product_wh_location_line_ids:
                    text += str(line.qty) + ' in ' + str(line.wh_location_id.name) +'\n'
                self.allocation = text
            else:
                raise ValidationError("Per riallocare devi mettere una quantità > 0 e un ripiano")

        if self.action == 'scraped':
            if not self.new_allocation:
                raise ValidationError("Devi scegliere una locazione da cui scaricare")
            
            decrease = False
            for line in self.product_id.product_wh_location_line_ids:
                if line.wh_location_id.id == self.new_allocation.id:
                    if line.qty < self.qty_to_move:
                        raise ValidationError("Non puoi spostare più prodotti di quanti ne contenga il ripiano")
                    decrease = True
                    line.decrease(self.qty_to_move)
            
            if not decrease:
                raise ValidationError("Hai scelto una allocazione in cui non è presente il prodotto")

            wh_stock = self.env.ref('stock.stock_location_stock')
            scraped_stock = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','=','reverse_scrape'),('company_id','=',self.env.user.company_id.id)])
            internal_move = self.env.ref('stock.picking_type_internal')
            if self.qty_to_move > 0:
                attr = {
                    'picking_type_id' : internal_move.id,
                    'move_type' : 'one',
                    'priority' : '1',
                    'location_id' : wh_stock.id,
                    'location_dest_id' : scraped_stock.operation.default_location_dest_id.id,
                    'move_lines' : [(0,0,{'product_id' : self.product_id.id, 'product_uom_qty' : self.qty_to_move ,
                        'state' : 'draft','product_uom' : self.product_id.uom_id.id, 'name' : 'WH/Strock > Magazzino Difettati'})],

                }
                pick = self.env['stock.picking'].create(attr)
                pick.action_confirm()
                pick.force_assign()
                pick.do_transfer()
                self.qty_available = self.product_id.qty_available
                text = ''
                for line in self.product_id.product_wh_location_line_ids:
                    text += str(line.qty) + ' in ' + str(line.wh_location_id.name) +'\n'
                self.allocation = text
            else:
                raise ValidationError("Per mettere in difettato il prodotto devi mettere una quantità > 0")

