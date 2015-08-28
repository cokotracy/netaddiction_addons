# -*- coding: utf-8 -*-

from openerp import models


class Product(models.Model):
    _inherit = 'product.product'

    def name_get(self, cr, user, ids, context=None):
        """
        Evita la visualizzazione del reference ID nel nome del prodotto.
        """
        if context is None or 'display_default_code' not in context:
            context = dict(context or {})
            context['display_default_code'] = False

        return super(Product, self).name_get(cr, user, ids, context)
