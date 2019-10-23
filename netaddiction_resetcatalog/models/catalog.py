# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
from odoo import models, api, _
from datetime import datetime

_logger = logging.getLogger(__name__)


class ResetCatalog(models.Model):

    _name = 'netaddiction.reset.catalog'

    def _deactive_products_no_available(self):
        # Deactive every product with no quantities and type product
        products = self.env['product.product'].search([
            ('qty_available', '<=', 0),
            ('type', '=', 'product'), ])
        # Deactive orderpoints
        orderpoints = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'in', products.ids),
            ])
        orderpoints.write({'active': False})
        products.write(
            {'sale_ok': False, 'active': False})
        _logger.info(_('{products} deactivated').format(
            products=len(products)))

    def _active_products_by_supplier_info(self):
        # Active every product that can be purchased from suppliers
        supplierinfos = self.env['product.supplierinfo'].search([
            ('avail_qty', '>', 0),
            ('product_id.active', '=', False),
            ])
        products = supplierinfos.mapped('product_id')
        products.write({'sale_ok': True, 'active': True})
        _logger.info(_('{products} activated').format(
            products=len(products)))
        supplierinfos.write({'avail_qty': 0})

    def _set_limit_on_product_available(self):
        # Active every product with quantity available
        products = self.env['product.product'].search([
            ('qty_available', '>', 0.0),
            ('type', '=', 'product'), ])
        products.write({
            'qty_limit': 0,
            'limit_action': 'no_purchasable'})
        _logger.info(_('{products} updated').format(
            products=len(products)))

    def _active_product_not_out_dated(self):
        # Active every product no out dated
        products = self.env['product.product'].search([
            ('out_date', '>=', datetime.today()),
            ('active', '=', False), ])
        products.write({'active': True})
        _logger.info(_('{products} activated').format(
            products=len(products)))
        products = products.filtered(
            lambda p: p.qty_available_now > p.qty_limit)
        products.write({'sale_ok': True})
        _logger.info(_('{products} updated').format(
            products=len(products)))

    @api.model
    def run_reset(self):
        _logger.info(_('Resetting Catalog'))
        _logger.info(_('Deactive products no available'))
        self._deactive_products_no_available()
        '''
        FIXME: Impossibile to use it until module with field 'avail_qty'
               is migrated (netaddiction_product)
        _logger.info(_('Active products purchasable'))
        self._active_products_by_supplier_info()
        '''
        _logger.info(_('Set limit on products available'))
        self._set_limit_on_product_available()
        '''
        FIXME: Impossibile to use it until PR #1 is migrated
        _logger.info(_('Active products not aout dated'))
        self._active_product_not_out_dated()
        '''
        _logger.info(_('Reset Catalog Done!'))
