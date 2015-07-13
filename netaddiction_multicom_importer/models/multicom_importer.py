# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Multicom_Importer(models.Model):
     _name = 'netaddiction.multiplayercom.importer'

     multiplayer_id = fields.Integer(string="Multiplayer.com ID")
     odoo_id = fields.Integer(string="Odoo ID")
     entity_type = fields.Selection((('product','Prodotto'),
     ('customer','Cliente'),('order','Ordine'),
     ('supplier','Fornitore'),('category','Categoria')),'Tipo')

     name = fields.Char("Nome", compute='_get_odoo_name')

     @api.one
     def _get_odoo_name(self):
         mapping = {
            'category' : 'product.category',
            'supplier' : 'res.partners',
            'order'    : 'sale.order',
            'customer' : 'res.partner',
            'product'  : 'product.product'
         }

         mod = self.env[mapping[self.entity_type]].browse([self.odoo_id])
         if(self.entity_type=='category'):
             self.name = mod.read(['complete_name'])[0]['complete_name']
         else:
             if self.entity_type == 'product':
                 self.name = mod.read(['name'])[0]['name']
                 tmpl_id = mod.read(['product_tmpl_id'])[0]['product_tmpl_id']
                 self.name += ' (template id: '+str(tmpl_id)+')'
             else:
                 self.name = mod.read(['name'])[0]['name']
