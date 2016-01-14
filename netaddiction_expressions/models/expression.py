# -*- coding: utf-8 -*-

from openerp import models, fields, api



class Condition(models.Model):
    _name = "netaddiction.expressions.condition"


    value = fields.Boolean(string="Valore", default=True)
    subject_type = fields.Selection([('category','Categoria'),('attribute','Attributo')], string='Tipo Soggetto',required=True)
    subject_id = fields.Integer(string = "Soggetto")
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
    def find_products(self):

        domain = []
        for condition in self.condition_ids:
            if condition.value:
                op = 'in'
            else:
                op = 'not in'

            if condition.subject_type == 'category':
                m1 = 'categ_id'
            else:
                m1 = 'attribute_value_ids'

            m2 = [condition.subject_id]
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


