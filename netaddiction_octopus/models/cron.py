import locale
import logging

from openerp import api, models

from ..base.registry import registry


_logger = logging.getLogger(__name__)


class Cron(models.Model):
    _name = 'netaddiction_octopus.cron'

    @api.model
    def run(self):
        Product = self.env['netaddiction_octopus.product']
        Supplier = self.env['netaddiction_octopus.supplier']

        self.clear()

        _logger.info('Divide!')

        suppliers = Supplier.search([(1, '=', 1)])

        for supplier in suppliers:
            if supplier.id != 6:  # TODO togliere
                continue  # TODO togliere

            _logger.info(' | %s (#%d)' % (supplier.name, supplier.id))

            handler = registry[supplier.handler](supplier.partner_id)

            categories = {
                (category['field'], category['code'] if category['field'].startswith('[field]') else None): {
                    'type': category['type'],
                    'category_id': category['category_id'],
                    'attribute_id': category['attribute_id'],
                } for category in supplier.category_ids}

            try:
                items = handler.pull()
            except Exception, e:
                _logger.warning(str(e))
            else:
                downloaded_products = len(items)
                rejected_products = 0
                discarted_products = 0

                _logger.info(' |  | Scaricato (%s prodotti)' % locale.format('%d', downloaded_products, grouping=True))

                for item in items:
                    try:
                        handler.validate(item)
                    except AssertionError:
                        rejected_products += 1
                        continue
                    else:
                        data = handler.mapping.map(Product, handler, item, categories)

                        if data is None:
                            discarted_products += 1
                            continue

                        Product.create(data)

                saved_products = downloaded_products - rejected_products

                _logger.info(' |  | Rifiutati (%s prodotti)' % locale.format('%d', rejected_products, grouping=True))
                _logger.info(' |  | Scartati (%s prodotti)' % locale.format('%d', discarted_products, grouping=True))
                _logger.info(' |  | Salvato (%s prodotti)' % locale.format('%d', saved_products, grouping=True))

        _logger.info('Impera!')

        barcodes = set(Product.search([(1, '=', 1)]).mapped('barcode'))

        for barcode in barcodes:
            products = Product.search([('barcode', '=', barcode)])

    def clear(self):
        self.env.cr.execute('DELETE FROM "netaddiction_octopus_product_product_attribute_value_rel"')
        self.env.cr.execute('DELETE FROM "netaddiction_octopus_product"')
        self.env.cr.execute('ALTER SEQUENCE "netaddiction_octopus_product_id_seq" RESTART WITH 1')
