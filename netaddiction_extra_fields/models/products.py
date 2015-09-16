# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Products(models.Model):
    _inherit = 'product.product'

    #campi override per rendere le varianti indipendenti dai template
    lst_price = fields.Float(string="Prezzo senza Iva")
    list_price = fields.Float(string="Prezzo Listino")
    seller_ids = fields.One2many('product.supplierinfo', 'product_vrnt_id', 'Supplier')

    #campi aggiunti
    published = fields.Boolean(string="Visibile sul Sito?")
    out_date = fields.Date(string="Data di Uscita")
    out_date_approx_type = fields.Selection(string="Approssimazione Data",
        selection=(('accurate','Preciso'),('month','Mensile'),('quarter','Trimestrale'),
        ('four','Quadrimestrale'),('year','Annuale')),
        help="""Impatta sulla vista front end,
        Preciso: la data inserita è quella di uscita,
        Mensile: qualsiasi data inserita prende solo il mese e l'anno (es: in uscita nel mese di Dicembre 2019),
        Trimestrale: prende l'anno e mese e calcola il trimestre(es:in uscita nel terzo trimestre 2019),
        Quadrimestrale: prende anno e mese e calcola il quadrimestre(es:in uscita nel primo quadrimestre del 2019),
        Annuale: prende solo l'anno (es: in uscita nel 2019)""" )

    #campo prezzo ivato
    final_price = fields.Float(string="Prezzo al pubblico")

    qty_available_now = fields.Integer(string="Quantità Disponibile",compute="_get_qty_available_now",
        help="Quantità Disponibile Adesso (qty in possesso - qty in uscita)")
    qty_sum_suppliers = fields.Integer(string="Quantità dei fornitori", compute="_get_qty_suppliers",
        help="Somma delle quantità dei fornitori")

    @api.one
    def _get_qty_available_now(self):
        self.qty_available_now = int(self.qty_available) - int(self.outgoing_qty)

    @api.one
    def _get_qty_suppliers(self):
        """
        somma, se ci sono, tutte le quantità dei fornitori
        """
        qty = 0
        for sup in self.seller_ids:
            qty = qty + int(sup.avail_qty)
        self.qty_sum_suppliers = qty

    @api.multi
    def write(self,values):
        """
        quando aggiorna il prodotto scorpora l'iva dal prezzo al pubblico
        """

        if len(self)==1:
            for p in self:
                tassa = p.taxes_id.amount
                final = p.final_price

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

    @api.model
    def create(self,values):
        if 'final_price' in values.keys() and 'taxes_id' in values.keys():
            id_tax = values['taxes_id'][0][2]
            if len(id_tax)>0:
                id_tax = id_tax[0]

            tassa = self.env['account.tax'].search([('id','=',id_tax)]).amount

            detax = values['final_price'] / (float(1) + tassa)
            deiva = round(detax,2)
            values['list_price'] = deiva

        return  super(Products, self).create(values)

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
        ('four','Quadrimestrale'),('year','Annuale')),
        help="""Impatta sulla vista front end,
        Preciso: la data inserita è quella di uscita,
        Mensile: qualsiasi data inserita prende solo il mese e l'anno (es: in uscita nel mese di Dicembre 2019),
        Trimestrale: prende l'anno e mese e calcola il trimestre(es:in uscita nel terzo trimestre 2019),
        Quadrimestrale: prende anno e mese e calcola il quadrimestre(es:in uscita nel primo quadrimestre del 2019),
        Annuale: prende solo l'anno (es: in uscita nel 2019)""")

    #campo prezzo ivato
    final_price = fields.Float(string="Prezzo al pubblico")

    #campi aggiunti per visualizzare anche le varianti con active=False
    #Valutare se mantenerli
    product_variant_count = fields.Integer(compute="_get_count_variants")


    @api.model
    def create(self,values):
        """
        questi sono alcuni campi separati che 'potrebbero' essere uguali tra
        template e varianti (sono comunque modificabili singolarmente)
        """
        new_id = super(Template, self).create(values)

        attr={k: v for k, v in values.items() if k in ['out_date','out_date_approx_type','active','published']}

        new_id.product_variant_ids.write(attr)

        return new_id

    @api.multi
    def write(self,values):

        attr={k: v for k, v in values.items() if k in ['out_date','out_date_approx_type','active','published']}

        self.product_variant_ids.write(attr)

        return super(Template, self).write(values)

    @api.one
    def _get_count_variants(self):
        """
        sovrascrivo il campo product_variant_count per contare anche i prodotti non attivi
        """
        searched = [('product_tmpl_id','=',self.id),'|',('active','=',False),('active','=',True)]
        result = self.env['product.product'].search(searched)
        self.product_variant_count = len(result)



class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    #campi aggiunti
    product_vrnt_id = fields.Many2one('product.product', 'Product', required=True, ondelete='cascade', select=True)
    avail_qty = fields.Float('Quantità disponibile',
        help="Il valore 0 non indica necessariamente l'assenza di disponibilità")
    base_price = fields.Float('Prezzo base', related='pricelist_ids.price')

    #uso le nuove api perchè sono più figo
    @api.model
    def create(self,values):
        """
        cerco il variant attuale,
        mi prendo il template e correggo
        """
        if 'product_tmpl_id' not in values:
            obj = self.env['product.product'].search([('id','=',values['product_vrnt_id'])])
            templ = obj.product_tmpl_id.id
            values['product_tmpl_id']=templ

        return super(SupplierInfo, self).create(values)


    #def create(self, cr, uid, vals, context=None):
    #    """
    #    Imposta la foreign key verso il template per mantenere la retrocompatibilità.
    #    """
    #    #vals['product_tmpl_id'] = context['active_id']

    #    return super(SupplierInfo, self).create(cr, uid, vals, context)
