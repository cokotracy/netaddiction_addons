# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
import datetime


class ExpressionExpression(models.Model):

    _name = 'netaddiction.expressions.expression'
    _rec_name = 'title'

    condition_ids = fields.One2many(
        'netaddiction.expressions.condition',
        'expression_id',
        string='Conditions',
        required=True
    )

    title = fields.Char(
        required=True
    )

    @api.multi
    def show_products(self):
        self.ensure_one()
        domain = []
        # Get domain from every condition
        for condition in self.condition_ids:
            domain.append(condition.get_domain())
        # Show products filtered by domain
        action = self.env.ref('stock.stock_product_normal_action').read()[0]
        action['domain'] = domain
        return action


class ExpressionCondition(models.Model):

    _name = 'netaddiction.expressions.condition'
    _descritpion = 'Conditions to search for every expression'

    attrib_id = fields.Many2one(
        'product.attribute.value',
        string='Attribute',
        ondelete='cascade',
        help='Specify a product Attribute '
        'if this rule only applies to products belonging to this attribute '
        'or its children categories. Keep empty otherwise.'
    )

    categ_id = fields.Many2one(
        'product.category',
        string='Category',
        ondelete='cascade',
        help='Specify a product category '
        'if this rule only applies to products belonging to this category '
        'or its children categories. Keep empty otherwise.'
    )

    expression_id = fields.Many2one(
        'netaddiction.expressions.expression',
        string="Expression"
    )

    value = fields.Boolean(
        default=True
    )

    operator = fields.Selection([
        ('<', 'Less than'),
        ('<=', 'Less or Equal than'),
        ('=', 'Equal'),
        ('>=', 'Greater or Equal than'),
        ('>', 'Greater than')]
    )

    out_date = fields.Date()

    subject_type = fields.Selection([
        ('category', 'Category'),
        ('attribute', 'Attribute'),
        ('available', 'In Stock'),
        ('preorder', 'In Reservation'),
        ('out_date', 'Out Date')
        ],
        required=True
    )

    @api.multi
    def _get_domain_category(self):
        self.ensure_one()
        operator = '=' if self.value else '!='
        to_search = 'categ_id'
        val = self.categ_id.id
        return (to_search, operator, val)

    @api.multi
    def _get_domain_attribute(self):
        self.ensure_one()
        to_search = 'attribute_value_ids'
        operator = 'in' if self.value else 'not in'
        val = self.attrib_id.id
        return (to_search, operator, val)

    @api.multi
    def _get_domain_available(self):
        self.ensure_one()
        operator = '>' if self.value else '<='
        to_search = 'qty_available'
        val = 0
        return (to_search, operator, val)

    @api.multi
    def _get_domain_preorder(self):
        self.ensure_one()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if self.value:
            to_search = 'out_date'
            operator = '>'
            val = today
        else:
            to_search = 'id'
            operator = 'not in'
            products = self.env['product.product'].search([
                '|', ('out_date', '>', today), ('out_date', '=', False)])
            val = products.ids
        return (to_search, operator, val)

    @api.multi
    def _get_domain_out_date(self):
        self.ensure_one()
        to_search = 'out_date'
        operator = self.operator
        val = self.out_date
        if operator == '<' or operator == '<=':
            products = self.env['product.product'].search([
                '|', ('out_date', '>', val), ('out_date', '=', False)])
            to_search = 'id'
            operator = 'not in'
            val = products.ids
        return (to_search, operator, val)

    @api.multi
    def get_domain(self):
        self.ensure_one()
        # Call the right function based on subject type value
        subject_type = self.subject_type
        function_to_call = getattr(self, f'_get_domain_{subject_type}')
        return function_to_call()
