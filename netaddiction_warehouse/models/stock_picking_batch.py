from collections import defaultdict

from odoo import api, fields, models

from ..tools.nawh_error import NAWHError as Error


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    # FORSE DA CAMBIARE IN_ENTRATA (in realtà se true è una lista purchase)
    in_exit = fields.Boolean(
        string="In uscita",
    )

    reverse_supplier = fields.Boolean(
        string="Resi a Fornitore",
    )

    product_list = fields.Many2many(
        'stock.move.line',
        compute='_get_list_product',
        string="Movimenti",
    )

    product_list_product = fields.Many2many(
        'product.product',
        compute='_get_list_product',
        string="Prodotti caricati/scaricati",
    )

    supplier = fields.Many2one(
        'res.partner',
        compute='_get_suppliers',
        search='_search_supplier',
        string="Fornitore",
    )

    date_done = fields.Datetime(
        compute='_get_date',
        search='_search_date',
        string="Data",
    )

    def _get_date(self):
        for batch in self:
            batch.date_done = batch.picking_ids[:1].date_done

    def _search_date(self, operator, value):
        return [('picking_ids.date_done', operator, value)]

    def _get_suppliers(self):
        # lo so è all'inverso ma non mi rompete le palle - Matteo -
        for batch in self:
            sup_id = False
            if batch.in_exit:
                sup_id = batch.picking_ids[:1].partner_id.id
            batch.update({'supplier': sup_id})

    def _search_supplier(self, operator, value):
        if operator not in ('=', 'ilike', 'like'):
            raise ValueError('Dominio invalido per il fornitore')
        return [
            ('picking_ids.partner_id.name', operator, value),
            ('in_exit', '=', True)
        ]

    def _get_list_product(self):
        for batch in self:
            products = []
            pids = []

            for pick in batch.picking_ids:
                for move_line in pick.move_line_ids:
                    if move_line.qty_done > 0:
                        products.append(move_line.id)
                        pids.append(move_line.product_id.id)

            batch.update({
                'product_list': [(6, 0, products)],
                'product_list_product': [(6, 0, pids)],
            })

    def get_product_list(self):
        """
        ritorna la lista dei prodotti e le quantità da pickuppare
        """
        self.ensure_one()

        wh_op_sett_obj = self.env['netaddiction.warehouse.operations.settings']
        scraped_type = wh_op_sett_obj.search(
            [('company_id', '=', self.env.user.company_id.id),
             ('netaddiction_op_type', '=', 'reverse_supplier_scraped')]
        )
        scrape_id = scraped_type.operation.id

        qtys = defaultdict(lambda: defaultdict(float))
        products = {}
        for picks in self.picking_ids:
            is_scraped = picks.picking_type_id.id == scrape_id

            for line in picks.move_line_ids:
                if not is_scraped:
                    qtys[line.product_id.barcode]['product_qty'] += line.product_qty
                    qtys[line.product_id.barcode]['qty_done'] += line.qty_done
                    qtys[line.product_id.barcode]['remaining_qty'] += line.qty_done - line.product_qty
                    qty_scraped = 0
                else:
                    qty_scraped = line.product_qty
                qtys[line.product_id.barcode]['qty_scraped'] += qty_scraped - line.qty_done
                qtys[line.product_id.barcode]['scraped_wh'] = 'dif'
                products[line.product_id] = qtys[line.product_id.barcode]

        return products

    @api.model
    def close_reverse(self, batch_id):
        batch = self.search([('id', '=', int(batch_id))])

        for out in batch.picking_ids:
            # se trovo almeno un riga con qty_done > 0 allora posso validare
            # l'ordine ed eventualmente creare il backorder
            validate = any(l.qty_done > 0 for l in out.move_line_ids)

            if validate:
                if out._check_backorder():
                    wiz_id = self.env['stock.backorder.confirmation'].create(
                        {'pick_ids': [(6, 0, out.ids)]}
                    )
                    wiz_id.process()
                    backorder_pick = self.env['stock.picking'].search(
                        [('backorder_id', '=', out.id)]
                    )
                    backorder_pick.write({'batch_id': None})
                else:
                    order = self.env['purchase.order'].search(
                        [('name', '=', out.origin)]
                    )
                    order.button_done()
                out.button_validate()
            else:
                out.write({'batch_id': None})

        batch.done()

    ##########################
    # INVENTORY APP FUNCTION #
    # ritorna un dict simile #
    # ad un json per il web  #
    ##########################

    @api.model
    def batch_pick_up(self, product_barcode, shelf_id, batch_id, qty_to_down):
        batch_id = int(float(batch_id)) if batch_id else False
        qty_to_down = int(float(qty_to_down)) if qty_to_down else 0
        result = self.search([('id', '=', batch_id)])
        if len(result) == 0:
            return Error(
                "Problema nel recuperare la lista prodotti o barcode mancante"
            )

        test = qty_to_down

        for res in result.picking_ids:
            if shelf_id == 'dif':
                res.pick_up_scraped(product_barcode, qty_to_down)
            elif test > 0:
                picked_qty = res.set_pick_up(product_barcode, shelf_id, test)
                test -= int(picked_qty)

    ##############################
    # END INVENTORY APP FUNCTION #
    ##############################

    ##########
    # CARICO #
    ##########

    @api.model
    def create_purchase_list(self, name, picking_orders):
        """
        crea una batch purhcase, nei picking_orders prende solo
        quelli non completati
        """
        ids = []
        for pick in picking_orders:
            for p in pick:
                res = self.env['stock.picking'].search(
                    [('id', '=', p),
                     ('state', '!=', 'done')]
                )
                ids.extend(res.ids)

        new_batch = self.create([{
            'name': name,
            'picking_ids': [(6, 0, ids)],
            'in_exit': True,
        }])

        return {'id': new_batch.id}

    @api.model
    def close_and_validate(self, batch):
        # prendo la locazione 0/0/0
        batch = self.search([('id', '=', int(batch))])
        loc_id = self.env['netaddiction.wh.locations'].search(
            [('barcode', '=', '0000000001')]
        )

        for out in batch.picking_ids:
            # se trovo almeno un riga con qty_done > 0 allora posso validare
            # l'ordine ed eventualmente creare il backorder
            validate = False
            for line in out.move_line_ids:
                if line.qty_done > 0:
                    validate = True
                    self.env['netaddiction.wh.locations.line'].allocate(
                        line.product_id.id, line.qty_done, loc_id.id)
                    line.product_id.qty_limit = 0

            if validate:
                if out._check_backorder():
                    wiz_id = self.env['stock.backorder.confirmation'].create(
                        {'pick_ids': [(4, out.id)]})
                    wiz_id.process()
                    backorder_pick = self.env['stock.picking'].search(
                        [('backorder_id', '=', out.id)])
                    backorder_pick.write({'batch_id': None})
                out.button_validate()

                origin = out.origin
                order = self.env['purchase.order'].search(
                    [('name', '=', origin)])
                if len(order.order_line) == 0:
                    order.state = 'cancel'
                    order.unlink()
                else:
                    close = True
                    for pick in order.picking_ids:
                        if pick.state not in ['cancel', 'done']:
                            close = False
                    if close:
                        order.button_done()
            else:
                out.write({'batch_id': None})

        batch.done()

    def done(self):
        '''
            This function is used as hook for every call to `batch.done()`
            in the code.
            `Batchs` are the old `waves` and waves had `done()`
            function to confirm them.
            To keep compatibility with migrated code
            we reintroduce this function
        '''
        #  Simulate Confirm on draft batchs
        draft_batchs = self.filtered(lambda b: b.state == 'draft')
        if draft_batchs:
            draft_batchs.action_confirm()
            self.refresh()
        #  Simulate Validate on confirmed batchs
        self.action_done()
