# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Products_Bonus(models.Model):
    _name = 'netaddiction.product.bonus'
    _inherits = {
        'product.product' : 'product_ref',
    }

    product_ref = fields.Many2one('product.product',ondelete="cascade",
        string="Prodotto Corrispondente",required="True")
    type = fields.Selection((('digital', 'Digitale'),('product','Prodotto Fisico')),
        string='Product Type',required="True")

    #uso domain per far si che i bonus vengano associati solo a prodotti normali
    #e non ad altri bonus
    bonus_parent_ids = fields.Many2many('product.product','product_bonus_rel',
        'op_bonus_id','op_product_id',string="Prodotti Associati",required="True",
        domain=[('is_bonus','=',False)])

    list_price = fields.Float(string="Prezzo di Vendita",default="0",readonly="True")

    @api.model
    def create(self, values):

        res_id = super(Products_Bonus, self).create(values)

        product = res_id.product_ref
        tmpl = product.product_tmpl_id

        # aggiorna i campi del template e del product in modo da metterli in linea con
        # il bonus
        if values['type'] == 'product':
            product.write({'type' : 'product','is_bonus': True})
            tmpl.write({'type' : 'product'})
        else:
            product.write({'type' : 'consu','is_bonus': True})
            tmpl.write({'type' : 'consu'})


        tmpl.write({'list_price' : 0,'lst_price' : 0})


        return res_id

    #override di unlink, così se viene cancellato il bonus,controlla prima
    #il prodotto referente
    @api.multi
    def unlink(self):
        for product in self.product_ref :
            product.unlink()
        return super(Products_Bonus, self).unlink()

    @api.multi
    def write(self,values):
        if 'type' in values.keys():
            if values['type']!='product':
                values['type']='consu'

        for product in self.product_ref :
            product.write(values)
            tmpl = product.product_tmpl_id
            tmpl.write(values)

        if values['type']=='consu':
            values['type']='digital'

        return super(Products_Bonus, self).write(values)

    # TODO: non visualizzare mai i prodotti bonus nel listato prodotti ???
    #       o comunque evitare modifiche lato product.product, si modifica solo lato product.bonus
    # TODO: aggiungere altre cose:
    # 2 - Altre funzionalità dei bonus, tipo i codici, il delivery dei codici etc.


class Product(models.Model):
    _inherit="product.product"

    bonus_products = fields.Many2many('netaddiction.product.bonus','product_bonus_rel',
        'op_product_id','op_bonus_id',string="Bonus Associati")

    #campo per identificare che il prodotto sia un bonus
    is_bonus = fields.Boolean(string="E' un Bonus?",default=False)
