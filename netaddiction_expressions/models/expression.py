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


    title = fields.Char(string="Nome", required=True)
    condition_ids = fields.One2many(
        comodel_name='netaddiction.expressions.condition',
        inverse_name='expression_id',
        string='Condizioni', required=True)

    @api.one
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


          
       # domain = [('categ_id', 'in', [6]),('attribute_value_ids','in', [7])]
        print domain

        view_id = self.env.ref('product.product_search_form_view').id
        print self.env['product.product'].search(domain)
        print view_id
        

        return {
            'name':'amamma',
            'view_type':'form',
            'view_mode':'tree, search, form',
            'views' : [(view_id,'search')],
            'res_model':'product.product',
            'search_view_id':view_id,
            'type':'ir.actions.act_window',
            'target': 'current',
            'filter_domain': domain,
#            'context' : {'search_default_categ_id' : [6]},
        }


