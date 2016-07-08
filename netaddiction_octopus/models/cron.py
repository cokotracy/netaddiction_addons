# -*- coding: utf-8 -*-

import locale
import logging

from collections import defaultdict

from openerp import api, models

from ..base.registry import registry


_logger = logging.getLogger(__name__)


class Cron(models.Model):
    _name = 'netaddiction_octopus.cron'

    @api.model
    def run(self):
        supplier_model = self.env['netaddiction_octopus.supplier']
        suppliers = {supplier.partner_id.id: supplier for supplier in supplier_model.search([(1, '=', 1)])}

        self.clear()
        self.divide(suppliers)
        # self.impera(suppliers)
        # self.kill(suppliers)

    def clear(self):
        self.env.cr.execute('DELETE FROM "netaddiction_octopus_product_product_attribute_value_rel"')
        self.env.cr.execute('DELETE FROM "netaddiction_octopus_product"')
        self.env.cr.execute('ALTER SEQUENCE "netaddiction_octopus_product_id_seq" RESTART WITH 1')

    def divide(self, suppliers):
        _logger.info('Divide!')

        product_model = self.env['netaddiction_octopus.product']

        for supplier in suppliers.values():
            _logger.info(' | %s (#%d)' % (supplier.name, supplier.id))

            datas = {}

            handler = registry[supplier.handler](supplier.partner_id)

            categories = {
                (category['field'], category['code'] if category['field'].startswith('[field]') else None): {
                    'type': category['type'],
                    'category_id': category['category_id'],
                    'attribute_id': category['attribute_id'],
                } for category in supplier.category_ids}

            taxes = {
                (tax['field'], tax['code'] if tax['field'].startswith('[field]') else None): {
                    'sale_tax_id': tax['sale_tax_id'],
                    'purchase_tax_id': tax['purchase_tax_id'],
                } for tax in supplier.tax_ids}

            # Downloading datas

            try:
                items = handler.pull()
            except Exception, e:
                _logger.warning(str(e))
            else:
                downloaded_products = len(items)
                rejected_products = 0
                discarted_products = 0

                _logger.info(' |  | Scaricato (%s prodotti)' % locale.format('%d', downloaded_products, grouping=True))

                # Mapping products

                for item in items:
                    try:
                        handler.validate(item)
                    except AssertionError:
                        rejected_products += 1
                        continue
                    else:
                        try:
                            data = handler.mapping.map(product_model, handler, item, categories, taxes)
                        except Exception, e:
                            _logger.warning(e)
                            rejected_products += 1
                            continue

                        if data is None:
                            discarted_products += 1
                            continue

                        datas[data['supplier_code']] = data

                # Checing for invalid groups

                groups = defaultdict(list)

                for data in datas.values():
                    groups[data['group_key']].append(data)

                for group_key, group in groups.items():
                    if len(group) > 1 and len(group) != len(set([str(p['attribute_ids']) for p in group])):
                        for data in group:
                            datas[data['supplier_code']].update({'group_key': None, 'group_name': None})

                # Saving products

                for data in datas.values():
                    product_model.create(data)

                # Reporting results

                saved_products = downloaded_products - rejected_products

                _logger.info(' |  | Rifiutati (%s prodotti)' % locale.format('%d', rejected_products, grouping=True))
                _logger.info(' |  | Scartati (%s prodotti)' % locale.format('%d', discarted_products, grouping=True))
                _logger.info(' |  | Salvato (%s prodotti)' % locale.format('%d', saved_products, grouping=True))

        # TODO migliorare organizzazione raggruppamento

        # for group_key, group in groups.items():
        #     if len(group) > 1 and len(group) != len(set([str(p['attribute_ids']) for p in group])):
        #         for i, product in enumerate(group):
        #             groups['%s%d' % (group_key, i)] = [product]

        #         del groups[group_key]

    def impera(self, suppliers):
        _logger.info('Impera!')

        product_model = self.env['netaddiction_octopus.product']

        invalid_barcodes = '', '0', '0000000000000'

        # Products with barcode

        products = product_model.search([('barcode', 'not in', invalid_barcodes), ('barcode', '!=', False)])
        barcodes = set(products.mapped('barcode'))

        for barcode in barcodes:
            products = product_model.search([('barcode', '=', barcode)])

            # IMPORTANT Addable products must preceed non-addable products
            products = sorted(products, key=lambda product: suppliers[product.supplier_id.id].can_add, reverse=True)

            for product in products:
                supplier = suppliers[product.supplier_id.id]

                try:
                    product.save(can_add=supplier.can_add)
                except Exception, e:
                    _logger.error('Salvaggio del prodotto non riuscito (%s)' % e)

        # Products without barcode

        products = product_model.search(['|', ('barcode', 'in', invalid_barcodes), ('barcode', '=', False)])

        for product in products:
            try:
                product.update(product)
            except Exception, e:
                _logger.error('Salvaggio del prodotto non riuscito (%s)' % e)

    def kill(self, suppliers):
        product_model = self.env['netaddiction_octopus.product']
        supplierinfo_model = self.env['product.supplierinfo']

        batch_size = 100

        for supplier_id in suppliers:
            products = product_model.search([('supplier_id', '=', supplier_id)]).mapped('supplier_code')

            for i in range(0, len(products), batch_size):
                supplierinfos = supplierinfo_model.search([
                    ('avail_qty', '>', 0),
                    ('name', '=', supplier_id),
                    ('product_code', 'not in', products[i:i + batch_size]),
                ])

                supplierinfos.write({'avail_qty': 0})
