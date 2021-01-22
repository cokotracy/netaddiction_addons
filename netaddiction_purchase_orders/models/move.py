# -*- coding: utf-8 -*-

from odoo import models, api
import locale
import datetime

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def app_cancel_backorder(self, datas, qty, context):
        moves = self.search([('id', 'in', datas['ids'])])
        to_delete = qty
        for move in moves:
            if to_delete > 0:
                new_qty = int(move.product_qty) - int(to_delete)
                if new_qty > 0:
                    move.sudo().product_uom_qty = new_qty
                    if move.sudo().purchase_line_id:
                        move.sudo().purchase_line_id.product_qty = move.sudo().purchase_line_id.qty_received + new_qty
                    for line in move.sudo().picking_id.pack_operation_product_ids:
                        if line.product_id.id == int(datas['product_id']):
                            line.sudo().product_qty = new_qty
                    to_delete = 0
                if new_qty <= 0:
                    move.sudo().action_cancel()
                    if move.sudo().purchase_line_id:
                        if move.sudo().purchase_line_id.qty_received + new_qty == 0:
                            move.sudo().purchase_line_id.unlink()
                        else:
                            move.sudo().purchase_line_id.product_qty = move.sudo().purchase_line_id.qty_received + new_qty
                    to_delete -= move.product_qty
                    origin = move.origin
                    order = self.env['purchase.order'].search([('name', '=', origin)])
                    if len(order.order_line) == 0:
                        order.sudo().state = 'cancel'
                        order.sudo().unlink()
                    else:
                        close = True
                        for pick in order.picking_ids:
                            if pick.state not in ['cancel', 'done']:
                                close = False
                        if close:
                            order.sudo().button_done()

        return True

    @api.model
    def log_change_backorder(self, supplier, product_name, sup_code, product_id, old_qty, new_qty, author_id, company):
        attr = {
            'author_id': int(author_id),
            'company_id': int(company),
            'field': supplier,
            'field_type': 'integer',
            'model_name': 'Cancellazione Backorder',
            'object_name': sup_code + ' - ' + product_name,
            'object_id': int(product_id),
            'old_value_integer': int(old_qty),
            'new_value_integer': int(new_qty)
        }
        self.env['netaddiction.log.line'].sudo().create(attr)

    # TODO The model netaddiction.log.line doesn't exist, adapt this code with the audit log
    # @api.model
    # def get_backorder_cancelled(self, ddate, company_id):
    #     if not ddate:
    #         ddate = datetime.date.today().strftime("%Y-%m-%d")

    #     results = self.env['netaddiction.log.line'].search(
    #         [
    #             ('create_date', '>=', ddate + ' 00:00:00'), 
    #             ('create_date', '<=', ddate + ' 23:59:59'), 
    #             ('model_name', '=', 'Cancellazione Backorder'), 
    #             ('company_id', '=', int(company_id))
    #         ], 
    #         order='field'
    #     )
    #     cancelled = {}
    #     for res in results:
    #         qty = res.old_value_integer - res.new_value_integer
    #         if int(res.field) not in cancelled:
    #             cancelled[int(res.field)] = {}
    #             supplier = self.env['res.partner'].browse(int(res.field))
    #             cancelled[int(res.field)]['supplier'] = supplier.name
    #             cancelled[int(res.field)]['products'] = {}
    #         if res.object_id not in cancelled[int(res.field)]['products']:
    #             cancelled[int(res.field)]['products'][res.object_id] = {}
    #             cancelled[int(res.field)]['products'][res.object_id]['qty'] = 0
    #             cancelled[int(res.field)]['products'][res.object_id]['product_name'] = res.object_name

    #         cancelled[int(res.field)]['products'][res.object_id]['qty'] += qty

    #     return cancelled

    @api.model
    def get_incoming_number_products_values(self):
        # ritorna un dict di fornitori che hanno prodotti in backorder con qta e valore
        results = self.search([('picking_type_id', '=', 1), ('state', 'not in', ['done', 'cancel'])])
        qtys = {}
        for res in results:
            if res.picking_id.partner_id:
                if res.picking_id.partner_id.id not in qtys:
                    qtys[res.picking_id.partner_id.id] = {'qty': 0, 'value': 0, 'ids': [], 'name': res.picking_id.partner_id.name}

                qtys[res.picking_id.partner_id.id]['qty'] += res.product_uom_qty
                qtys[res.picking_id.partner_id.id]['value'] += res.purchase_line_id.price_unit * res.product_uom_qty
                qtys[res.picking_id.partner_id.id]['ids'].append(res.id)

        return qtys

    @api.model
    def get_incoming_products_supplier(self, supplier, context):
        # ritorna un dict di prodotti per il fornitore supplier
        # qta, valore, ids stock.move corrispondenti
        if not supplier:
            return 'Errore'

        results = self.search([('picking_type_id', '=', 1), ('state', 'not in', ['done', 'cancel']), ('picking_id.partner_id.id', '=', int(supplier))])
        datas = {}

        for res in results:
            if res.product_id.id not in datas:

                supplier_code = ''
                for sup_line in res.product_id.seller_ids:
                    if sup_line.name.id == int(supplier):
                        supplier_code = sup_line.product_code

                datas[res.product_id.id] = {
                    'product_name': res.product_id.with_context(context).display_name,
                    'product_id': res.product_id.id,
                    'qty': 0,
                    'value': 0,
                    'value_locale': '',
                    'supplier_code': supplier_code,
                    'qty_available': res.product_id.qty_available_now,
                    'ids': []
                }

            datas[res.product_id.id]['qty'] += res.product_uom_qty
            datas[res.product_id.id]['value'] += res.purchase_line_id.price_unit * res.product_uom_qty
            # FIXME this locale.setlocale() give an error 
            #  locale.Error: unsupported locale setting
            # locale.setlocale(locale.LC_ALL, 'it_IT.UTF8')
            # datas[res.product_id.id]['value_locale'] = locale.format("%.2f", datas[res.product_id.id]['value'], grouping=True)
            datas[res.product_id.id]['value_locale'] = datas[res.product_id.id]['value']
            datas[res.product_id.id]['ids'].append(res.id)

        return datas
