# -*- coding: utf-8 -*-

from openerp import models, fields, api



class Condition(models.Model):
    _name = "netaddiction.expressions.condition"


    value = fields.Boolean(string="Incluso?", default=True)
    #subject_type = fields.Selection([('category','Categoria'),('attribute','Attributo'),('product','Prodotto')], string='Tipo Soggetto',required=True)
    # subject_id = fields.Integer(string = "Soggetto")
    #product_id = fields.Many2one(comodel_name ='product.product', string='Prodotto', ondelete='cascade', help="Specify a product if this rule only applies to one product. Keep empty otherwise.")
    subject_type = fields.Selection([('category','Categoria'),('attribute','Attributo')], string='Tipo Soggetto',required=True)
    categ_id = fields.Many2one(comodel_name ='product.category', string='Categoria', ondelete='cascade', help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise.")
    attrib_id = fields.Many2one(comodel_name ='product.attribute.value', string='Attributo', ondelete='cascade', help="Specify a product Attribute if this rule only applies to products belonging to this attribute or its children categories. Keep empty otherwise.")
    expression_id = fields.Many2one(comodel_name='netaddiction.expressions.expression',
        string="Espressione")

class Expression(models.Model):
    _name = "netaddiction.expressions.expression"
    _rec_name = 'title'


    title = fields.Char(string="Titolo", required=True)
    condition_ids = fields.One2many(
        comodel_name='netaddiction.expressions.condition',
        inverse_name='expression_id',
        string='Condizioni', required=True)

 

    @api.multi
    def find_products_view(self):

        domain = []
        for condition in self.condition_ids:
            op = '=' if condition.value else '!='

            if condition.subject_type == 'category':
                m1 = 'categ_id'
                m2 = condition.categ_id.id
            elif condition.subject_type == 'attribute':
                m1 = 'attribute_value_ids'
                m2 = condition.attrib_id.id
            # elif condition.subject_type == 'product':
            #     m1 = 'id'
            #     m2 = condition.product_id.id

    
            domain.append((m1,op,m2))

        view_id = self.env.ref('product.product_product_tree_view').id

        return {
            'name':'Lista Prodotto Espressione',
            'view_type':'form',
            'view_mode':'tree, form',
            'views' : [(view_id,'tree')],
            'res_model':'product.product',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'domain': domain,
            'context' : {},
        }

    @api.multi
    def find_products_domain(self):

        domain = []
        for condition in self.condition_ids:
            op = '=' if condition.value else '!='

            if condition.subject_type == 'category':
                m1 = 'categ_id'
                m2 = condition.categ_id.id
            elif condition.subject_type == 'attribute':
                m1 = 'attribute_value_ids'
                m2 = condition.attrib_id.id
            # elif condition.subject_type == 'product':
            #     m1 = 'id'
            #     m2 = condition.product_id.id

    
            domain.append((m1,op,m2))

        return domain


