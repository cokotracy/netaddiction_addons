from odoo.tests.common import TransactionCase


class TestCatalog(TransactionCase):

    def setUp(self):
        super(TestCatalog, self).setUp()
        self.product_model = self.env['product.product']
        self.catalog_model = self.env['netaddiction.reset.catalog']

    def test_deactive_products_no_available(self):
        filters = [('qty_available', '<=', 0),
                   ('type', '=', 'product'), ]
        self.catalog_model._deactive_products_no_available()
        products = self.product_model.search(filters)
        self.assertEqual(len(products), 0)
        products_deactivated = self.product_model.search(
            filters + [('active', '=', False)])
        self.assertEqual(products.ids, products_deactivated.ids)
        orderpoints = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'in', products.ids),
            ])
        self.assertEqual(len(orderpoints), 0)

    def test_active_products_by_supplier_info(self):
        # FIXME: To use when function will be integrated
        pass

    def test_set_limit_on_product_available(self):
        products = self.env['product.product'].search([
            ('qty_available', '>', 0.0),
            ('type', '=', 'product'), ])
        self.catalog_model._set_limit_on_product_available()
        products_updated = self.env['product.product'].search([
            ('qty_available', '>', 0.0),
            ('type', '=', 'product'), ])
        self.assertEqual(products.ids, products_updated.ids)

    def test_active_product_not_out_dated(self):
        # FIXME: To use when function will be integrated
        pass
