# -*- coding: utf-8 -*-

import logging

from base64 import b64encode
from operator import xor

from openerp import models, fields
from openerp.addons.decimal_precision import get_precision

from ..base.downloaders import HTTPDownloader


_logger = logging.getLogger(__name__)


class Template(models.Model):
    _inherit = 'product.template'

    octopus_group = fields.Char('Gruppo Octopus', index=True)


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
    sale_tax_id = fields.Many2one('account.tax', string='Tassa di vendita')
    purchase_tax_id = fields.Many2one('account.tax', string='Tassa di acquisto')
    company_id = fields.Many2one('res.company', 'Società')
    group_key = fields.Char('Chiave gruppo')
    group_name = fields.Char('Nome gruppo')

    def save(self, can_add=False, commit=True):
        if self.barcode is None:
            supplierinfo = self.env['product.supplierinfo'].search([
                ('name', '=', self.supplier_id.id),
                ('product_code', '=', self.supplier_code),
            ])

            if supplierinfo.exists():
                return self.update(supplierinfo, commit=commit)
        else:
            product = self.env['product.product'].search([
                ('barcode', '=', self.barcode),
                '|', ('active', '=', False), ('active', '=', True)
            ])

            if product.exists():
                supplierinfo = product.seller_ids.search([
                    ('name', '=', self.supplier_id.id),
                    ('product_code', '=', self.supplier_code),
                ])

                if supplierinfo.exists():
                    return self.update(supplierinfo, commit=commit)

                return self.chain(product, commit=commit)

            if can_add:
                return self.add(commit=commit)

    def add(self, commit=True):
        image = None
        template_id = None

        create_context = {
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
            'mail_notrack': True,
        }

        if self.image:
            try:
                raw_image = HTTPDownloader().download(self.image, raw=True)
            except Exception, e:
                _logger.error("Download non riuscito per l'immagine %s (%s)" % (self.image, e.message))
            else:
                image = b64encode(raw_image)

        if self.group_key:
            template_id = self.env['product.template'].search([('octopus_group', '=', self.group_key)]).id

        product = self.env['product.product'].with_context(create_context).create({
            'product_tmpl_id': template_id,
            'name': self.group_name or self.name,
            'barcode': self.barcode,
            'company_id': self.company_id.id,
            'final_price': self.price,
            'out_date_approx_type': 'accurate',
            'out_date': self.date,
            'description': self.description,
            'categ_id': self.category_id.id,
            'property_cost_method': 'real',
            'property_valuation': 'real_time',
            'image': image,
            'type': 'product',
            'taxes_id': [(4, self.sale_tax_id.id, None)],
            'supplier_taxes_id': [(4, self.purchase_tax_id.id, None)],
            'seller_ids': [(0, None, {
                'company_id': self.company_id.id,
                'name': self.supplier_id.id,
                'product_name': self.group_name or self.name,
                'product_code': self.supplier_code,
                'avail_qty': self.supplier_quantity,
                'price': self.supplier_price,
            })],
        })

        if self.group_key and not template_id:
            product.product_tmpl_id.write({'octopus_group': self.group_key})

        if commit:
            self.env.cr.commit()

    def chain(self, product, commit=True):
        product.write({
            'seller_ids': [(0, None, {
                'company_id': self.company_id.id,
                'name': self.supplier_id.id,
                'product_name': self.name,
                'product_code': self.supplier_code,
                'avail_qty': self.supplier_quantity,
                'price': self.supplier_price,
            })],
        })

        if commit:
            self.env.cr.commit()

    def update(self, product=None, supplierinfo=None, commit=True):
        if not xor(product is None, supplierinfo is None):
            raise Exception('You must specify a product or a supplier info')

        if product is not None:
            supplierinfo = self.env['product.supplierinfo'].search([
                ('name', '=', self.supplier_id.id),
                ('product_code', '=', self.supplier_code),
            ])

        supplierinfo.write({
            'avail_qty': self.supplier_quantity,
            'price': self.supplier_price,
        })

        if commit:
            self.env.cr.commit()
