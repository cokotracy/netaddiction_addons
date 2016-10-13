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
    percentage_discount = fields.Integer(string="Percentuale di sconto")

class product_pricelist(models.Model):
    _inherit = "product.pricelist"

    expression = fields.Many2many(comodel_name='pricelist.condition', string='Espressioni')

    carrier_price = fields.Float(string="Costo Spedizione")
    carrier_gratis = fields.Float(string="Spedizione Gratis se valore maggiore di", default=0)

    percent_price = fields.Float(string="Percentuale default(sconto)")

    search_field = fields.Char(string="Cerca prodotti")

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

            # TODO: le due query sottostanti possono essere evitate perché
            # in products_by_qty_by_partner ci sono già i prodotti
            objs = self.pool('product.product').search(cr, uid, [('id', '=', int(pid))])
            obj = self.pool('product.product').browse(cr, uid, objs, context=context)

            # tassa = obj.taxes_id.amount

            # if tassa:
            #    detax = obj.offer_price / (float(1) + float(tassa/100))
            # else:
            #    detax = obj.offer_price

            # offer_detax = round(detax, 2)

            real_price = obj.offer_price if (obj.offer_price > 0 and obj.offer_price < price) else price

            results[pid] = (real_price, other_val)

        return results

    @api.one
    def populate_item_ids_from_expression(self):
        if self.expression:
            pids = []
            for line in self.item_ids:
                pids.append(line.product_id.id)
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