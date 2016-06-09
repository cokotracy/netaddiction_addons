# -*- coding: utf-8 -*-

import logging

from datetime import date, datetime
from hashlib import md5
from pysolr import SolrError

from openerp import api, models

from ..base.client import Solr


_logger = logging.getLogger(__name__)


class ProductMixin(object):
    SOLR_TRACKED_FIELDS = (
        'name',
        'description',
        'barcode',
        'final_price',
        'special_price',
        'taxes_id',
        'supplier_taxes_id',
        'attribute_value_ids',
        'categ_id',
        'active',
        'sale_ok',
        'visible',
        'out_date',
        'available_date',
        'offer_catalog_lines',
        'offer_cart_lines',
    )

    @staticmethod
    def push_to_solr(*documents):
        solr = Solr.get()

        try:
            solr.add(documents)
        except SolrError, e:
            _logger.warning(e)

    @staticmethod
    def remove_from_solr(*ids):
        solr = Solr.get()

        try:
            solr.delete(q='id:(%s)' % ' OR '.join(ids))
        except SolrError, e:
            _logger.warning(e)

    @property
    def solr_document_id(self):
        fields = (
            self.company_id.id,
            self._name,
            self.id,
        )

        document_id = md5(''.join([str(field) for field in fields])).hexdigest()

        return document_id

    @property
    def solr_document(self):
        today = date.today()
        out_date = datetime.strptime(self.out_date, '%Y-%m-%d').date() if self.out_date else None
        available_date = datetime.strptime(self.available_date, '%Y-%m-%d').date() if self.available_date else None

        return {
            'id': self.solr_document_id,
            'model': self._name,
            'company_id': self.company_id.id,
            'name': self.name,
            'description': self.description,
            'barcode': self.barcode,
            'category': self.categ_id.name,
            'date': out_date if out_date else available_date,
            'price': self.offer_price if self.offer_price else self.final_price,
            'is_available': self.qty_available_now > 0,
            'is_offer': len(self.offer_catalog_lines) + len(self.offer_cart_lines) > 0,
            'is_preorder': out_date is not None and out_date > today or available_date is not None and available_date > today,
        }

    def can_push_to_solr(self):
        return self.active and self.sale_ok and self.visible

    @api.constrains(*SOLR_TRACKED_FIELDS)
    def pickup_for_solr(self):
        if self.can_push_to_solr():
            self.push_to_solr(self.solr_document)
        else:
            self.remove_from_solr(self.solr_document_id)


class Product(models.Model, ProductMixin):
    _inherit = 'product.product'


class Template(models.Model, ProductMixin):
    SOLR_TRACKED_FIELDS = (
        'name',
        'description',
        'taxes_id',
        'supplier_taxes_id',
        'categ_id',
        'active',
        'sale_ok',
        'visible',
        'out_date',
        'available_date',
    )

    _inherit = 'product.template'

    @api.constrains(*SOLR_TRACKED_FIELDS)
    def pickup_for_solr(self):
        to_add, to_remove = [], []

        for product in self.product_variant_ids:
            if product.can_push_to_solr():
                to_add.append(product.solr_document)
            else:
                to_remove.append(product.solr_document_id)

        if to_add:
            self.push_to_solr(*to_add)

        if to_remove:
            self.remove_from_solr(*to_remove)
