# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class Pricelist(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(selection=(
        ('list_price', 'Prezzo di vendita'),
        ('final_price', 'Prezzo di listino')
    ), string="Basato su", required=True)

class ProductPricelistCondition(models.Model):
    _name = "pricelist.condition"

    expression = fields.Many2one(comodel_name='netaddiction.expressions.expression', string='Espressione')
    percentage_discount = fields.Integer(string="Percentuale")
    typology = fields.Selection(selection=(
        ('discount', 'Sconto'),
        ('inflation', 'Rincaro')
    ), string="Tipo Listino", required=False, default="discount")

class product_pricelist(models.Model):
    _inherit = "product.pricelist"

    expression = fields.Many2many(comodel_name='pricelist.condition', string='Espressioni')

    carrier_price = fields.Float(string="Costo Spedizione")
    carrier_gratis = fields.Float(string="Spedizione Gratis se valore maggiore di", default=0)

    percent_price = fields.Float(string="Percentuale default(sconto)")

    search_field = fields.Char(string="Cerca prodotti")

    @api.multi
    def write(self ,values):
        return super(product_pricelist,self).write(values)

    @api.multi
    def search_product(self):
        self.ensure_one()
        dom = [('pricelist_id', '=', self.id), ('product_id.name', 'ilike', self.search_field)]
        self.search_field = ''
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cerca Prodotti in listino: %s' % self.name,
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'product.pricelist.item',
            'view_id': False,
            'views': [(False, 'tree')],
            'target': 'current',
            'domain': dom,
            'context': self.env.context}

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        """
        Serve a dare il prezzo corretto alla pricelist: se l'offer_price è inferiore al prezzo dell'attuale pricelist
        allore restituisco l'offer price.
        """
        results = super(product_pricelist, self)._price_rule_get_multi(cr, uid, pricelist, products_by_qty_by_partner,
            context=context)

        for pid in results:
            price = results[pid][0]
            other_val = results[pid][1]
            real_price = 0
            # prendo il rigo della pricelist per vedere se è una scontistica o un rincaro
            rows = self.pool("product.pricelist.item").search(cr, uid, [('id', '=', int(other_val))])
            row = self.pool('product.pricelist.item').browse(cr, uid, rows, context=context)
            
            if row:
                obj = row[0].product_id
                if row[0].typology == 'inflation':
                    per = row[0].percent_price / 100
                    purchase = row[0].purchase_price
                    percent = purchase * per
                    real_price = purchase + percent
                    # deve tornare iva inclusa
                    real_price = row[0].product_id.supplier_taxes_id.compute_all(real_price)['total_included']
                else:
                    per = row[0].percent_price / 100
                    percent = obj.final_price * per
                    real_price = obj.final_price - percent
                real_price = obj.special_price if (obj.special_price > 0 and obj.special_price < real_price) else real_price
                real_price = obj.offer_price if (obj.offer_price > 0 and obj.offer_price < real_price) else real_price
                results[pid] = (real_price, other_val)

        return results

    @api.model
    def cron_updater(self):
        pricelist = self.search([('active', '=', True)])
        for price in pricelist:
            if price.expression:
                price.populate_item_ids_from_expression()

    @api.one
    def populate_item_ids_from_expression(self):
        if self.expression:
            pids = []
            lines = {}
            for line in self.item_ids:
                pids.append(line.product_id.id)
                lines[line.product_id.id] = line
                if line.qty_available_now <= line.qty_lmit_b2b:
                    line.unlink()
            for expr in self.expression:
                dom = expr.expression.find_products_domain()
                for prod in self.env['product.product'].search(dom):
                    attr = {
                        'applied_on': '0_product_variant',
                        'product_id': prod.id,
                        'compute_price': 'formula',
                        'base': 'final_price',
                        'price_discount': expr.percentage_discount,
                        'pricelist_id': self.id,
                        'percent_price': expr.percentage_discount,
                        'typology': expr.typology,
                    }
                    if prod.id not in pids:
                        self.env['product.pricelist.item'].create(attr)
        else:
            raise ValidationError("Se non metti un'espressione non posso aggiungere prodotti")

    @api.one
    def delete_all_items(self):
        self.item_ids.unlink()

class ProductPriceItems(models.Model):
    _inherit = "product.pricelist.item"

    b2b_real_price = fields.Float(string="Prezzo reale", compute="_get_real_price")
    typology = fields.Selection(selection=(
        ('discount', 'Sconto'),
        ('inflation', 'Rincaro')
    ), string="Tipo Listino", required=False, default="discount")
    qty_lmit_b2b = fields.Integer("Quantità Limite B2B", default=0)

    qty_available_now = fields.Integer("Quantità Disponibile", related="product_id.qty_available_now")
    purchase_price = fields.Float("Prezzo Di Acquisto", compute="_get_purchase_price")

    @api.one
    def _get_purchase_price(self):
        if self.product_id:
            if self.qty_available_now > 0:
                self.purchase_price = self.product_id.med_inventory_value
            else:
                # se non è disponibile:
                # 1) cerco l'ultimo carico
                # 2) prezzo medio fornitori
                po = self.env['purchase.order.line'].search([('product_id', '=', self.product_id.id)], order='create_date desc', limit=1)
                if po:
                    self.purchase_price = po[0].price_unit
                else:
                    price = 0
                    num = 0
                    for sup in self.product_id.seller_ids:
                        num += 1
                        price += sup.price
                    self.purchase_price = price / num

    @api.one
    def _get_real_price(self):
        if self.product_id:
            price = self.pricelist_id.price_rule_get(self.product_id.id, 1)
            # qua faccio i ltry perchè nella creazione della nuova pricelist non ha subito l'id e succede un casino se non salvi prima
            try:
                prid = self.pricelist_id.id
                self.b2b_real_price = self.product_id.taxes_id.compute_all(price[prid][0])['total_excluded']
            except:
                pass

    @api.multi
    def open_form_item(self):
        return {
            'type': 'ir.actions.act_window',
            'name': '%s' % self.display_name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

class Products(models.Model):
    _inherit = 'product.product'

    b2b_price = fields.Char(string="Prezzi B2B", compute="_compute_b2b_price")

    @api.one
    def _compute_b2b_price(self):
        result = self.env['product.pricelist.item'].search([('product_id.id', '=', self.id)])
        if result:
            text = ''
            for res in result:
                if res.pricelist_id.id:
                    price = res.pricelist_id.sudo().price_rule_get(self.id, 1)
                    b2b = self.taxes_id.compute_all(price[res.pricelist_id.id][0])
                else:
                    b2b = self.taxes_id.compute_all(self.final_price)
                b2b_iva = b2b['total_included']
                b2b_noiva = b2b['total_excluded']
                text += '%s - %s [%s]; ' % (res.pricelist_id.name, str(round(b2b_noiva, 2)).replace('.', ','), str(round(b2b_iva, 2)).replace('.', ','))
            self.b2b_price = text
        else:
            self.b2b_price = ''
