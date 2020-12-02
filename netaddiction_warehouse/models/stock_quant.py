import base64
import csv
import io
import locale

from datetime import date, datetime

from odoo import api, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def get_supplier(self):
        self.ensure_one()
        pick_type_in = self.env.ref('stock.picking_type_in')
        sup = False

        # FIXME: history_ids non esiste più
        # for history in self.history_ids:
        #     if history.picking_type_id == pick_type_in:
        #         sup = history.picking_partner_id

        return sup

    @api.model
    def get_inventory_at_date(self, from_date, to_date, company_id):
        # prendo tutte le movimentazioni tra oggi e inv_date
        # sommo algebricamente rispetto alla quantità attuale del prodotto
        # e avrò la quantità in inv_date
        # ciò che non è stato movimentato evidentemente era così già allora
        # per la valorizzazione devo trovare la quant corrispondente alla move
        # e comportarmi come per le qty
        moves = self.env['stock.move'].search(
            [('state', '=', 'done'),
             ('company_id', '=', company_id),
             ('date', '>=', from_date),
             ('date', '<=', to_date)]
        )
        inventory = {}
        location = self.env.ref('stock.stock_location_stock')
        for move in moves:
            if move.product_id in inventory:
                # operi in base alla movimentazione
                # se proviene da wh allora è un + (è uscito)
                # se arriva a wh lo devi togliere rispetto a oggi
                if move.location_id == location:
                    inventory[move.product_id]['qty'] += move.product_uom_qty
                elif move.location_dest_id == location:
                    inventory[move.product_id]['qty'] -= move.product_uom_qty
            else:
                inventory[move.product_id] = {}
                inventory[move.product_id]['qty'] = move.product_id.qty_available
                if move.location_id == location:
                    inventory[move.product_id]['qty'] += move.product_uom_qty
                elif move.location_dest_id == location:
                    inventory[move.product_id]['qty'] -= move.product_uom_qty

        print(inventory)

    @api.model
    def reports_inventario(self, domain, supplier_results):
        products = self.env['product.product'].search(domain)
        output = io.BytesIO()
        writer = csv.writer(output)
        csvdata = [
            'Categoria',
            'Prodotto',
            'Sku',
            'Barcode',
            'Qty Allocata',
            'Valore Medio Unitario',
            'Valore Totale',
            'Prezzo di Vendita',
            'Scaffali'
        ]
        writer.writerow(csvdata)
        locale.setlocale(locale.LC_ALL, 'it_IT.UTF8')
        for prod in products:
            # TODO: se suppleir_results metti i valori di quel fornitore sicuro
            tot_inventory = prod.qty_available * prod.med_inventory_value
            price = prod.intax_price
            if prod.offer_price:
                price = prod.offer_price
            med = prod.med_inventory_value

            tot_inventory = locale.format("%.2f", tot_inventory, grouping=True)
            price = locale.format("%.2f", price, grouping=True)
            med = locale.format("%.2f", med, grouping=True)

            csvdata = [
                prod.categ_id.display_name.encode('utf8'),
                prod.with_context({'lang': 'it_IT', 'tz': 'Europe/Rome'}).display_name.encode('utf8'),
                str(prod.id),
                str(prod.barcode),
                int(prod.qty_available),
                med,
                tot_inventory,
                price
            ]
            for line in prod.product_wh_location_line_ids:
                text = str(line.qty) + ' ' + line.wh_location_id.name
                csvdata.append(text)
            writer.writerow(csvdata)

        data = base64.b64encode(output.getvalue()).decode()
        output.close()

        now = datetime.now()
        return self.env['ir.attachment'].create({
            'name': 'export %s.csv' % now,
            'datas_fname': 'export %s.csv' % now,
            'type': 'binary',
            'datas': data
        }).id

    @api.model
    def inventory_csv(self):
        wh = self.env.ref('stock.stock_location_stock').id
        quants = self.search([('location_id', '=', wh)])
        products = {}
        for quant in quants:
            if quant.product_id.id in products:
                products[quant.product_id.id]['qty'] += int(quant.qty)
                products[quant.product_id.id]['inventory_value'] += round(quant.inventory_value, 2)
            else:
                products[quant.product_id.id] = {
                    'name': quant.product_id.display_name,
                    'category': quant.product_id.categ_id.display_name,
                    'qty': int(quant.qty),
                    'inventory_value': round(quant.inventory_value, 2),
                }
                text = ''
                for loc in quant.product_id.product_wh_location_line_ids:
                    text += '| %s - %s |' % (loc.wh_location_id.name, loc.qty)
                products[quant.product_id.id]['location'] = text

        output = io.BytesIO()
        writer = csv.writer(output)
        csvdata = [
            'Categoria',
            'Prodotto',
            'Quantità',
            'Valore Totale',
            'Scaffali'
        ]
        writer.writerow(csvdata)
        for product in products:
            csvdata = [
                products[product]['category'].encode('utf8'),
                products[product]['name'].encode('utf8'),
                products[product]['qty'],
                products[product]['inventory_value'],
                products[product]['location']
            ]
            writer.writerow(csvdata)
        data = base64.b64encode(output.getvalue()).decode()
        output.close()
        return self.env['ir.attachment'].create({
            'name': 'export %s' % date.today(),
            'type': 'binary',
            'datas': data
        })

    @api.model
    def get_quant_from_supplier(self, supplier_id):
        wh = self.env.ref('stock.stock_location_stock')
        quants = self.search(
            [('company_id', '=', self.env.user.company_id.id),
             ('location_id', '=', wh.id),
             # FIXME: history_ids non esiste più
             # ('history_ids.picking_id.partner_id.id', '=', int(supplier_id)),
             # FIXME: reservation_id non esiste più
             # ('reservation_id', '=', False)
            ]
        )
        quant_data = {}
        for quant in quants:
            if quant.product_id.id in quant_data:
                quant_data[quant.product_id.id]['qty'] += quant.qty
                quant_data[quant.product_id.id]['inventory_value'] += quant.inventory_value
                quant_data[quant.product_id.id]['single_inventory'] = quant.inventory_value / quant.qty
            else:
                quant_data[quant.product_id.id] = {
                    'id': quant.product_id.id,
                    'name': quant.product_id.display_name,
                    'qty': quant.qty,
                    'inventory_value': quant.inventory_value,
                    'single_inventory': quant.inventory_value / quant.qty
                }
        return quant_data

    @api.model
    def get_scraped_from_supplier(self, supplier_id):
        wh_op_sett = self.env['netaddiction.warehouse.operations.settings']
        scraped_stock = wh_op_sett.search(
            [('netaddiction_op_type', '=', 'reverse_scrape'),
             ('company_id', '=', self.env.user.company_id.id)]
        )
        wh = scraped_stock.operation.default_location_dest_id.id
        quants = self.search(
            [('company_id', '=', self.env.user.company_id.id),
             ('location_id', '=', wh),
             # FIXME: history_ids non esiste più
             # ('history_ids.picking_id.partner_id.id', '=', int(supplier_id)),
             # FIXME: reservation_id non esiste più
             # ('reservation_id', '=', False)
             ]
        )
        quant_data = {}
        for quant in quants:
            if quant.product_id.id in quant_data:
                quant_data[quant.product_id.id]['qty'] += quant.qty
                quant_data[quant.product_id.id]['inventory_value'] += quant.inventory_value
                quant_data[quant.product_id.id]['single_inventory'] = quant.inventory_value / quant.qty
            else:
                quant_data[quant.product_id.id] = {
                    'id': quant.product_id.id,
                    'name': quant.product_id.display_name,
                    'qty': quant.qty,
                    'inventory_value': quant.inventory_value,
                    'single_inventory': quant.inventory_value / quant.qty
                }
        return quant_data

    # TODO: QUESTO METODO NON ESISTE PIÙ, ERA UN OVERRIDE DEL METODO STANDARD
    # TODO:     CHE ELIMINAVA UN CONTROLLO (a riga 247)
    def _prepare_account_move_line(self, cr, uid, move, qty, cost,
                                   credit_account_id, debit_account_id,
                                   context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        if context.get('force_valuation_amount'):
            valuation_amount = context.get('force_valuation_amount')
        else:
            if move.product_id.cost_method == 'average':
                valuation_amount = cost if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal' else move.product_id.standard_price
            else:
                valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        valuation_amount = currency_obj.round(cr, uid,
                                              move.company_id.currency_id,
                                              valuation_amount * qty)
        # check that all data is correct
        # if move.company_id.currency_id.is_zero(valuation_amount):
        #    raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (move.product_id.name,))
        partner_id = (move.picking_id.partner_id and self.pool.get(
            'res.partner')._find_accounting_partner(
            move.picking_id.partner_id).id) or False
        debit_line_vals = {
            'name': move.name,
            'product_id': move.product_id.id,
            'quantity': qty,
            'product_uom_id': move.product_id.uom_id.id,
            'ref': move.picking_id and move.picking_id.name or False,
            'partner_id': partner_id,
            'debit': valuation_amount > 0 and valuation_amount or 0,
            'credit': valuation_amount < 0 and -valuation_amount or 0,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': move.name,
            'product_id': move.product_id.id,
            'quantity': qty,
            'product_uom_id': move.product_id.uom_id.id,
            'ref': move.picking_id and move.picking_id.name or False,
            'partner_id': partner_id,
            'credit': valuation_amount > 0 and valuation_amount or 0,
            'debit': valuation_amount < 0 and -valuation_amount or 0,
            'account_id': credit_account_id,
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
