from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductsMovement(models.TransientModel):
    _name = 'netaddiction.products.movement'
    _description = "Netaddiction Products Movement"

    action = fields.Selection(
        [('scraped', 'Difettato'),
         ('rialloca', 'Rialloca'),
         ('down', 'Scarica')],
        required=True,
        string="Azione",
    )

    allocation = fields.Text(
        string="Allocazioni"
    )

    barcode = fields.Char(
        string="Barcode"
    )

    new_allocation = fields.Many2one(
        'netaddiction.wh.locations',
        string="Dove Allocare/Scaricare",
    )

    product_id = fields.Many2one(
        'product.product',
        string="Prodotto",
    )

    qty_available = fields.Integer(
        string="Qtà in magazzino"
    )

    qty_to_move = fields.Integer(
        string="Quantità da muovere o riallocare"
    )

    @api.onchange('barcode')
    def _get_product_from_barcode(self):
        product = self.env['product.product'].search(
            [('barcode', '=', self.barcode)],
            limit=1
        )
        if product:
            self.update_data_from_product(product)

    @api.onchange('product_id')
    def _get_products_data(self):
        self.update_data_from_product()

    def execute(self):
        self.ensure_one()
        return getattr(self, 'execute_action_{}'.format(self.action))

    def execute_action_down(self):
        self.ensure_one()
        if not self.product_id:
            raise ValidationError("Devi scegliere un prodotto")

        if self.qty_to_move > 0 and self.new_allocation:
            line = self.env['netaddiction.wh.locations.line'].search(
                [('product_id', '=', self.product_id.id),
                 ('wh_location_id', '=', self.new_allocation.id)],
                limit=1
            )
            if not line:
                raise ValidationError(
                    "Ripiano da cui scaricare errato, non è presente"
                    " nessuna quantità di questo prodotto"
                )

            line.decrease(self.qty_to_move)
            self.update_data_from_product()
        else:
            raise ValidationError(
                "Per Scaricare devi mettere una quantità > 0 e un ripiano"
            )

    def execute_action_rialloca(self):
        self.ensure_one()
        if not self.product_id:
            raise ValidationError("Devi scegliere un prodotto")

        if self.qty_to_move > 0 and self.new_allocation:
            self.env['netaddiction.wh.locations.line'].allocate(
                self.product_id.id,
                self.qty_to_move,
                self.new_allocation.id
            )
            self.update_data_from_product()
        else:
            raise ValidationError(
                "Per riallocare devi mettere una quantità > 0 e un ripiano"
            )

    def execute_action_scraped(self):
        self.ensure_one()
        if not self.product_id:
            raise ValidationError("Devi scegliere un prodotto")

        if not self.new_allocation:
            raise ValidationError(
                "Devi scegliere una locazione da cui scaricare"
            )

        wh_op_sett_obj = self.env['netaddiction.warehouse.operations.settings']
        pick_obj = self.env['stock.picking']

        decrease = False
        for line in self.product_id.product_wh_location_line_ids:
            if line.wh_location_id.id == self.new_allocation.id:
                if line.qty < self.qty_to_move:
                    raise ValidationError(
                        "Non puoi spostare più prodotti di quanti ne"
                        " contenga il ripiano"
                    )
                decrease = True
                line.decrease(self.qty_to_move)

        if not decrease:
            raise ValidationError(
                "Hai scelto una allocazione in cui non è presente il prodotto"
            )

        wh_stock = self.env.ref('stock.stock_location_stock')
        scraped_stock = wh_op_sett_obj.search(
            [('netaddiction_op_type', '=', 'reverse_scrape'),
             ('company_id', '=', self.env.user.company_id.id)]
        )
        internal_move = self.env.ref('stock.picking_type_internal')
        if self.qty_to_move > 0:
            pick = pick_obj.create({
                'picking_type_id': internal_move.id,
                'move_type': 'one',
                'priority': '1',
                'location_id': wh_stock.id,
                'location_dest_id': scraped_stock.operation
                .default_location_dest_id.id,
                'move_lines': [
                    (0, 0, {
                        'product_id': self.product_id.id,
                        'product_uom_qty': self.qty_to_move,
                        'state': 'draft',
                        'product_uom': self.product_id.uom_id.id,
                        'name': 'WH/Strock > Magazzino Difettati'
                    })
                ],
            })
            pick.action_confirm()
            pick.force_assign()
            pick.do_transfer()
            self.update_data_from_product()
        else:
            raise ValidationError(
                "Per mettere in difettato il prodotto devi mettere una"
                " quantità > 0"
            )

    def update_data_from_product(self, product=None):
        self.ensure_one()
        product = product or self.product_id
        self.update({
            'allocation': "\n".join([
                "{} in {}".format(str(l.qty), l.wh_location_id.name)
                for l in product.product_wh_location_line_ids
            ]),
            'barcode': product.barcode,
            'product_id': product.id,
            'qty_available': product.qty_available,
        })
