from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase


class TestExpression(TransactionCase):

    def _create_product(self, values):
        return self.env['product.product'].create(values)

    def _create_product_for_preorder(self):
        values = {
            'name': 'Product example for preorder',
            'out_date': self.today
        }
        return self._create_product(values)

    def _create_product_for_out_date(self):
        yesterday = (self.today - timedelta(days=1))
        values = {
            'name': 'Product example for out date',
            'out_date': yesterday
        }
        return self._create_product(values)

    def _create_expression(self, values):
        return self.env['netaddiction.expressions.expression'].create(values)

    def _create_expression_for_category(self):
        values = {
            'title': 'Expression example for category',
            'condition_ids': [(0, 0, {
                'subject_type': 'category',
                'categ_id': self.consumable_categ_id.id,
                'value': True,
                })]
        }
        return self._create_expression(values)

    def _create_expression_for_attribute(self):
        values = {
            'title': 'Expression example for attribute',
            'condition_ids': [(0, 0, {
                'subject_type': 'attribute',
                'attrib_id': self.color_black_attribute_id.id,
                'value': True,
                })]
        }
        return self._create_expression(values)

    def _create_expression_for_available(self):
        values = {
            'title': 'Expression example for available',
            'condition_ids': [(0, 0, {
                'subject_type': 'available',
                'value': True,
                })]
        }
        return self._create_expression(values)

    def _create_expression_for_preorder(self):
        values = {
            'title': 'Expression example for preorder',
            'condition_ids': [(0, 0, {
                'subject_type': 'preorder',
                'value': True,
                })]
        }
        return self._create_expression(values)

    def _create_expression_for_out_date(self):
        values = {
            'title': 'Expression example for out date',
            'condition_ids': [(0, 0, {
                'subject_type': 'out_date',
                'operator': '<',
                'out_date': self.today,
                'value': True,
                })]
        }
        return self._create_expression(values)

    def setUp(self):
        super(TestExpression, self).setUp()
        self.consumable_categ_id = self.env.ref(
            'product.product_category_consumable')
        self.color_black_attribute_id = self.env.ref(
            'product.product_attribute_2')
        self.today = datetime.today()
        # Create products
        self.product_for_preorder = self._create_product_for_preorder()
        self.product_for_out_date = self._create_product_for_out_date()

    def _test_expression(self, expression, products):
        action = expression.show_products()
        products_to_show = self.env['product.product'].search(
            action['domain'])
        self.assertEqual(products, products_to_show)

    def test_simple_category(self):
        expression = self._create_expression_for_category()
        # Get all products with category "Consumable"
        products = self.env['product.product'].search([
            ('categ_id', '=', self.consumable_categ_id.id),
            ])
        self._test_expression(expression, products)

    def test_simple_attribute(self):
        expression = self._create_expression_for_attribute()
        # Get all products with attribute "Color: Black"
        products = self.env['product.product'].search([
            ('attribute_value_ids', '=', self.color_black_attribute_id.id),
            ])
        self._test_expression(expression, products)

    def test_simple_available(self):
        expression = self._create_expression_for_available()
        # Get all products available
        products = self.env['product.product'].search([
            ('qty_available', '>', 0.0),
            ])
        self._test_expression(expression, products)

    def test_simple_preorder(self):
        expression = self._create_expression_for_preorder()
        # Get all products in preorder
        self._create_product_for_preorder()
        products = self.env['product.product'].search([
            ('out_date', '>', self.today),
            ])
        self._test_expression(expression, products)

    def test_simple_out_date(self):
        expression = self._create_expression_for_out_date()
        # Get all products with out date before today
        self._create_product_for_out_date()
        products = self.env['product.product'].search([
            ('out_date', '<', self.today),
            ])
        self._test_expression(expression, products)
