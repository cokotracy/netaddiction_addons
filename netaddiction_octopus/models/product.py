# -*- coding: utf-8 -*-

from openerp import models, fields
from openerp.addons.decimal_precision import get_precision


class Product(models.Model):
    _name = 'netaddiction_octopus.product'

    barcode = fields.Char('Barcode', index=True)
    supplier_id = fields.Many2one('res.partner', string='Fornitore', domain=[('supplier', '=', True)])
    supplier_code = fields.Char('Codice fornitore')
    supplier_price = fields.Float('Prezzo fornitore', digits_compute=get_precision('Product Price'))
    supplier_quantity = fields.Float('Quantità fornitore')
    name = fields.Char('Nome')
    description = fields.Text('Descrizione')
    price = fields.Float('Prezzo', digits_compute=get_precision('Product Price'))
    image = fields.Char('Immagine')
    date = fields.Date('Data')
    category_id = fields.Many2one('product.category', string='Categoria')
    attribute_ids = fields.Many2many('product.attribute.value', string='Attributi')
    is_pending = fields.Boolean('In attesa', index=True)
    is_processed = fields.Boolean('Processato', index=True)
    company_id = fields.Many2one('res.company', 'Società')
