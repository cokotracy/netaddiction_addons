# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from collections import defaultdict

class OrdersReverse(models.Model):
    _inherit = "sale.order"

    count_reverse = fields.Integer(string="# Resi",compute="_count_reverse")

    is_reversible = fields.Boolean(string="Reversibile" ,compute="is_reversible_func")


    @api.one
    def _count_reverse(self):
        """
        Si prende i settings per i resi ['reverse_scrape','reverse_resale']
        Trova tutti i picking effettuati per queste tipologie 
        Li conta e aggiorna count_reverse
        """
        picking_type_id = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','in',['reverse_scrape','reverse_resale']),('company_id','=',self.env.user.company_id.id)])
        ids = []
        for i in picking_type_id:
            ids.append(i.operation.id)
        picking = self.env['stock.picking'].search([('origin','=',self.name),('picking_type_id','in',ids)])
        self.count_reverse = len(picking)

    @api.one
    def is_reversible_func(self):
        """
        Prende tutti i resi per questo sale.order.
        Ogni rigo reso lo confronta con i righi ordine e per ogni rigo estre le quantità di quel prodotto da 
        poter ancora rendere.
        Se la quantità dda poter rendere è maggiore di zero allora ritorna True
        """
        picking_type_id = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','in',['reverse_scrape','reverse_resale']),('company_id','=',self.env.user.company_id.id)])
        ids = []
        for i in picking_type_id:
            ids.append(i.operation.id)
        picking = self.env['stock.picking'].search([('origin','=',self.name),('picking_type_id','in',ids)])
        pick_pids = defaultdict(float)
        for pick in picking:
            for line in pick.pack_operation_product_ids:
                if line.product_id.id in pick_pids.keys():
                    pick_pids[line.product_id.id] += line.qty_done
                else:
                    pick_pids[line.product_id.id] = line.qty_done

        to_reverse = defaultdict(float)
        for line in self.order_line:
            if line.product_id.id in pick_pids.keys():
                qta = line.qty_delivered - pick_pids[line.product_id.id]
                if qta > 0:
                    if line.product_id.id in to_reverse.keys():
                        to_reverse[line.product_id.id] += qta
                    else:
                        to_reverse[line.product_id.id] = qta
            else:
            	if(line.qty_delivered) > 0:
                	to_reverse[line.product_id.id] = line.qty_delivered

        if len(to_reverse)==0:
        	self.is_reversible = False
        else:
        	self.is_reversible = True

        return to_reverse

    #action view per i resi
    @api.multi
    def open_reverse(self):
        picking_type_id = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','in',['reverse_scrape','reverse_resale']),('company_id','=',self.env.user.company_id.id)])
        ids = []
        for i in picking_type_id:
            ids.append(i.operation.id)
        view_id = self.env['ir.ui.view'].search([('name','=','stock.vpicktree')])
        action = {
            'type': 'ir.actions.act_window',
            'res_model': "stock.picking",
            'view_id': view_id.id,
            'view_mode': 'tree,form',
            'target': 'current',
            'domain' : [('origin','=',self.name),('picking_type_id','in',ids)],
            'context': {},
            'name' : 'Resi per ordine %s' % self.name
        }
        return action

    @api.multi
    def get_payment(self):
        """
        ritorna il metodo di pagamento usato o presunto dal pagamento
        dipende strettamente da netaddiction_payments
        """
        self.ensure_one()

        if len(self.account_payment_ids) > 0:
            return self.account_payment_ids[0]

        return False

class OrderLineReverse(models.Model):
    _inherit = "sale.order.line"

    qty_reverse = fields.Integer(string = "Reso", compute = "_get_qty_reverse")

    stock_line_ids = fields.Many2many(string="Linee spedizione collegate",comodel_name="stock.pack.operation")

    @api.one
    def _get_qty_reverse(self):
        """
        Conta la quantità resa per quel rigo ordine
        """
        picking_type_id = self.env['netaddiction.warehouse.operations.settings'].search([('netaddiction_op_type','in',['reverse_scrape','reverse_resale']),('company_id','=',self.env.user.company_id.id)])
        ids = []
        for i in picking_type_id:
            ids.append(i.operation.id)
        picking = self.env['stock.picking'].search([('origin','=',self.order_id.name),('picking_type_id','in',ids)])

        reverse = 0
        for pick in picking:
            for line in pick.pack_operation_product_ids:
                if line.product_id.id == self.product_id.id:
                    reverse += line.qty_done

        self.qty_reverse = reverse