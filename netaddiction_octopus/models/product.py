# -*- coding: utf-8 -*-
import logging
from base64 import b64encode
from operator import xor
from odoo import api, fields, models
from ..base.downloaders import HTTPDownloader
import requests, json


_logger = logging.getLogger(__name__)


class Template(models.Model):
    _inherit = 'product.template'

    octopus_group = fields.Char(
        'Gruppo Octopus',
        index=True
    )


class Product(models.Model):
    _name = 'netaddiction_octopus.product'
    _description = 'Octopus Product'

    attribute_ids = fields.Many2many(
       'product.attribute.value',
       string='Attributi'
    )

    barcode = fields.Char(
        'Barcode',
        index=True
    )

    category_id = fields.Many2one(
       'product.category',
        string='Categoria'
    )

    company_id = fields.Many2one(
       'res.company',
       string='Società'
    )

    date = fields.Date(
       string='Data'
    )

    description = fields.Text(
       string='Descrizione'
    )

    group_key = fields.Char(
        string='Chiave gruppo'
    )

    group_name = fields.Char(
        string='Nome gruppo'
    )

    image = fields.Char(
       string='Immagine'
    )

    is_new = fields.Boolean(
        'Nuovo',
        default=False
    )

    name = fields.Char(
       string='Nome'
    )

    price = fields.Float(
       string='Prezzo',
       digits='Product Price'
    )

    purchase_tax_id = fields.Many2one(
       'account.tax',
       string='Tassa di acquisto'
    )

    sale_tax_id = fields.Many2one(
       'account.tax',
       string='Tassa di vendita'
    )

    supplier_code = fields.Char(
        string='Codice fornitore'
    )

    supplier_id = fields.Many2one(
        'res.partner',
        string='Fornitore',
        domain=[('supplier', '=', True)]
    )

    supplier_price = fields.Float(
       'Prezzo fornitore',
       digits='Product Price'
    )

    supplier_quantity = fields.Float(
       string='Quantità fornitore'
    )

    '''
    @api.multi
    def import_product(self):
        self.ensure_one()
        self.is_new = False
        # eventualmente metto qua l'import dell'immagine
        # devo farlo solo per i prodotti che non ce l'hanno
        if not self.image:
            self.search_image_qwant()
        product = self.add(active=False)
        return {
            'name': 'Importazione prodotti Octopus',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': product.id,
        }

    @api.multi
    def blacklist_product(self):
        self.ensure_one()
        self.env['netaddiction_octopus.blacklist'].create({
            'supplier_id': self.supplier_id.id,
            'supplier_code': self.supplier_code,
        })
        self.unlink()
    '''

    def deferred_save(self, can_add=False, commit=True):
        if self.barcode is None:
            supplierinfo = self.env['product.supplierinfo'].search([
                ('name', '=', self.supplier_id.id),
                ('product_code', '=', self.supplier_code),
            ])
            if supplierinfo:
                return self.update(supplierinfo, commit=commit)
        else:
            product = self.env['product.product'].search([
                ('barcode', '=', self.barcode),
                '|', ('active', '=', False), ('active', '=', True)
            ])
            if product:
                supplierinfo = product.seller_ids.search([
                    ('name', '=', self.supplier_id.id),
                    ('product_code', '=', self.supplier_code),
                ])
                if supplierinfo:
                    return self.update(supplierinfo, commit=commit)
                return self.chain(product, commit=commit)
            if can_add:
                self.is_new = True

    '''
    def add(self, commit=True, active=True):
        image = None
        template_id = None
        context = {
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
            'mail_notrack': True,
        }
        if self.image:
            try:
                raw_image = HTTPDownloader().download(self.image, raw=True)
            except Exception:
                _logger.error(
                    "Download non riuscito per l'immagine %s (%s)" % (
                        self.image, e.message))
            else:
                image = b64encode(raw_image)
        if self.group_key:
            template_id = self.env['product.template'].search(
                [('octopus_group', '=', self.group_key)]).id
        if self.attribute_ids and self.group_name:
            name = self.group_name
        else:
            name = self.name
        product = self.env['product.product'].with_context(context).create({
            'active': active,
            'product_tmpl_id': template_id,
            'name': name,
            'barcode': self.barcode,
            'company_id': self.company_id.id,
            'final_price': self.price,
            'out_date_approx_type': 'accurate',
            'out_date': self.date,
            'description': self.description,
            'categ_id': self.category_id.id,
            'attribute_value_ids': [(4, attribute.id, None)
                                    for attribute
                                    in self.attribute_ids],
            'property_cost_method': 'real',
            'property_valuation': 'real_time',
            'image': image,
            'type': 'product',
            'taxes_id': [(4, self.sale_tax_id.id, None)],
            'supplier_taxes_id': [(4, self.purchase_tax_id.id, None)],
            'seller_ids': [(0, None, {
                'company_id': self.company_id.id,
                'name': self.supplier_id.id,
                'product_name': name,
                'product_code': self.supplier_code,
                'avail_qty': self.supplier_quantity,
                'price': self.supplier_price,
            })],
        })
        if self.group_key and not template_id:
            product.product_tmpl_id.write({'octopus_group': self.group_key})
        if commit:
            self.env.cr.commit()
        return product

    def chain(self, product, commit=True):
        context = {}
        product.with_context(context).write({
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
    '''

    def deferred_update(self, supplierinfo=None, commit=True):
        if supplierinfo is None:
            supplierinfo = self.env['product.supplierinfo'].search([
                ('name', '=', self.supplier_id.id),
                ('product_code', '=', self.supplier_code),
            ])
        # Aggiunge l'immagine ai prodotti che ancora non ne hanno una
        if self.image and False:
            product = supplierinfo.product_id
            if not product.image:
                try:
                    raw_image = HTTPDownloader().download(self.image, raw=True)
                except Exception:
                    _logger.error(
                        "Download non riuscito per l'immagine %s (%s)" % (
                            self.image, e.message))
                else:
                    image = b64encode(raw_image)

                product.image = image

                if commit:
                    self.env.cr.commit()
        update_mapping = {
            'avail_qty': 'supplier_quantity',
            'price': 'supplier_price',
        }
        context = {}
        # Aggiorna *supplierinfo*
        # solo se i campi in *update_mapping* sono cambiati
        for supplierinfo_field, self_field in update_mapping.items():
            if getattr(supplierinfo,
                       supplierinfo_field) != getattr(self, self_field):
                data = {
                    si_field: getattr(self, self_field)
                    for si_field, self_field
                    in update_mapping.items()
                    }
                supplierinfo.with_context(context).write(data)
                if commit:
                    self.env.cr.commit()
                break

