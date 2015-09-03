# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Products(models.Model):
    _inherit = 'product.product'

    #campi override per rendere le varianti indipendenti dai template
    type = fields.Selection((('consu', 'Consumable'),('service','Service'),
        ('product','Prodotto Stoccabile')), string='Tipo Prodotto', _translate="True")
    lst_price = fields.Float(string="Prezzo senza Iva")
    list_price = fields.Float(string="Prezzo Listino")
    seller_ids = fields.One2many('product.supplierinfo', 'product_vrnt_id', 'Supplier')

    #campi aggiunti
    published = fields.Boolean(string="Visibile sul Sito?")
    out_date = fields.Date(string="Data di Uscita")
    out_date_approx_type = fields.Selection(string="Approssimazione Data",
        selection=(('accurate','Preciso'),('month','Mensile'),('quarter','Trimestrale'),
        ('four','Quadrimestrale'),('year','Annuale')))

    #campo prezzo ivato
    final_price = fields.Float(string="Prezzo al pubblico")

    @api.multi
    def write(self,values):
        tassa = self.taxes_id.amount
        final = self.final_price

        if 'taxes_id' in values.keys():
            id_tax = values['taxes_id'][0][2]
            if len(id_tax)>0:
                id_tax = id_tax[0]

            tassa = self.env['account.tax'].search([('id','=',id_tax)]).amount

        if 'final_price' in values.keys():
            final = values['final_price']

        detax = final / (float(1) + tassa)
        deiva = round(detax,2)
        values['list_price'] = deiva

        return super(Products, self).write(values)

        @api.multi
        def create(self,values):
            tassa = self.taxes_id.amount
            final = self.final_price

            if 'taxes_id' in values.keys():
                id_tax = values['taxes_id'][0][2]
                if len(id_tax)>0:
                    id_tax = id_tax[0]

                tassa = self.env['account.tax'].search([('id','=',id_tax)]).amount

            if 'final_price' in values.keys():
                final = values['final_price']

            detax = final / (float(1) + tassa)
            deiva = round(detax,2)
            values['list_price'] = deiva

            return super(Products, self).create(values)

class Template(models.Model):
    _inherit = 'product.template'

    #campi override per rendere le varianti indipendenti dai template
    type = fields.Selection((('consu', 'Consumable'),('service','Service'),
        ('product','Prodotto Stoccabile')), string='Tipo Prodotto', _translate="True")
    lst_price = fields.Float(string="Prezzo senza Iva")
    list_price = fields.Float(string="Prezzo Listino")

    #campi aggiunti
    published = fields.Boolean(string="Visibile sul Sito?")
    out_date = fields.Date(string="Data di Uscita")
    out_date_approx_type = fields.Selection(string="Approssimazione Data",
        selection=(('accurate','Preciso'),('month','Mensile'),('quarter','Trimestrale'),
        ('four','Quadrimestrale'),('year','Annuale')))

    #campo prezzo ivato
    final_price = fields.Float(string="Prezzo al pubblico")



class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    #campi aggiunti
    product_vrnt_id = fields.Many2one('product.product', 'Product', required=True, ondelete='cascade', select=True)
    avail_qty = fields.Float('Quantità disponibile',
        help="Il valore 0 non indica necessariamente l'assenza di disponibilità")
    base_price = fields.Float('Prezzo base', related='pricelist_ids.price')

    def create(self, cr, uid, vals, context=None):
        """
        Imposta la foreign key verso il template per mantenere la retrocompatibilità.
        """
        vals['product_tmpl_id'] = context['active_id']
        
        return super(SupplierInfo, self).create(cr, uid, vals, context)
