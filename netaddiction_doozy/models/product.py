# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.tools.translate import _


class Product(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.depends('qty_available')
    def _product_available_text(self, *args, **kwargs):
        """
        Evita che la quantità venga mostrata con i decimali.
        """
        self.qty_available_text = str(int(self.qty_available)) + _(' On Hand')

    qty_available_text = fields.Char(compute=_product_available_text)

    def name_get(self, cr, user, ids, context=None):
        """
        Evita la visualizzazione del reference ID nel nome del prodotto.
        """
        if context is None or 'display_default_code' not in context:
            context = dict(context or {})
            context['display_default_code'] = False

        return super(Product, self).name_get(cr, user, ids, context)

class Template(models.Model):
    _inherit = 'product.template'

    @api.one
    @api.depends('qty_available')
    def _product_available_text(self, *args, **kwargs):
        """
        Evita che la quantità venga mostrata con i decimali.
        """
        self.qty_available_text = str(int(self.qty_available)) + _(' On Hand')

    qty_available_text = fields.Char(compute=_product_available_text)


    #se riesco a fare l'override forse posso fare il redirect sul bonus
