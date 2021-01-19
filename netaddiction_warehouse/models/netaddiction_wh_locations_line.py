from odoo import models, fields, api
from ..tools.nawh_error import NAWHError


class NetaddictionWhLocationsLine(models.Model):
    _name = 'netaddiction.wh.locations.line'
    _description = "Netaddiction WH Locations Line"
    _order = 'qty'

    product_id = fields.Many2one(
        'product.product',
        required=True,
        string="Prodotto",
    )

    qty = fields.Integer(
        default=1,
        required=True,
        string="Quantità",
    )

    wh_location_id = fields.Many2one(
        'netaddiction.wh.locations',
        required=True,
        string="Ripiano",
    )

    @api.model
    def get_products(self, barcode):
        """
        dato il barcode di un ripiano ritorna i prodotti allocati
        """
        result = self.search([('wh_location_id.barcode', '=', barcode)])
        if not result:
            return NAWHError(
                "Non sono stati trovati prodotti per il barcode"
            )
        return result

    ##########################
    # INVENTORY APP FUNCTION #
    # ritorna un dict simile #
    # ad un json per il web  #
    ##########################

    @api.model
    def get_json_products(self, barcode):
        """
        ritorna un json con i dati per la ricerca per ripiano
        """
        is_shelf = self.env['netaddiction.wh.locations'].check_barcode(barcode)
        if isinstance(is_shelf, NAWHError):
            return {'result': 0, 'error': is_shelf.msg}

        results = self.get_products(barcode)
        if isinstance(results, NAWHError):
            return {'result': 0, 'error': results.msg}

        return {
            'result': 1,
            'shelf': is_shelf.name,
            'barcode': barcode,
            'products': [
                {'product_name': res.product_id.display_name,
                 'qty': res.qty,
                 'barcode': res.product_id.barcode}
                for res in results
            ]
        }

    @api.model
    def put_json_new_allocation(self, barcode, qty, product_id, now_wh_line):
        """
        sposta la quantità qty dal ripiano barcode al new_shelf
        """
        is_shelf = self.env['netaddiction.wh.locations'].check_barcode(barcode)

        if isinstance(is_shelf, NAWHError):
            return {'result': 0, 'error': is_shelf.msg}

        new_shelf = is_shelf.id

        line = self.search(
            [('id', '=', int(now_wh_line)),
             ('product_id', '=', int(product_id))]
        )

        if not line:
            return {
                'result': 0,
                'error': 'Prodotto non più presente in questa locazione'
            }

        if line.wh_location_id.id == new_shelf:
            return {
                'result': 0,
                'error': 'Non puoi spostare un prodotto nella'
                         ' stessa locazione di partenza'
            }

        dec = line.decrease(qty)
        if isinstance(dec, NAWHError):
            return {'result': 0, 'error': dec.msg}

        self.allocate(product_id, qty, new_shelf)

        product = self.env['product.product'].browse(int(product_id))
        return {'result': 1, 'product_barcode': product.barcode}

    ##############################
    # END INVENTORY APP FUNCTION #
    ##############################

    ##################
    # FUNZIONI VARIE #
    ##################

    def decrease(self, qta):
        """ decrementa la quantità allocata di qta """
        self.ensure_one()
        end_qty = self.qty - int(qta)

        if end_qty < 0:
            return NAWHError(
                "Non puoi scaricare una quantità maggiore di quella allocata"
            )
        elif end_qty > 0:
            self.write({'qty': end_qty})
        else:
            self.unlink()

    def increase(self, qta):
        """ incrementa la quantità allocata di qta """
        self.ensure_one()
        self.qty += int(qta)

    @api.model
    def allocate(self, product_id, qta, new_location_id):
        """ alloca in new_location_id la qta di product_id """
        result = self.search(
            [('product_id', '=', int(product_id)),
             ('wh_location_id', '=', int(new_location_id))]
        )

        if result:
            # è già presente una locazione con questo prodotto
            # incremento
            for res in result:
                res.increase(qta)
        else:
            self.create([{
                'product_id': product_id,
                'qty': qta,
                'wh_location_id': new_location_id
            }])
