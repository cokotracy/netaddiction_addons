# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Products(models.Model):
    _inherit = 'product.product'

    #separazione listini di acquisto
    seller_ids = fields.One2many('product.supplierinfo', 'product_id', 'Supplier')
    #separazione prezzo di  vendita e creazione prezzo ivato e senza iva
    lst_price = fields.Float(string="Prezzo senza Iva")
    list_price = fields.Float(string="Prezzo Listino")
    #campo prezzo ivato
    final_price = fields.Float(string="Prezzo al pubblico")
    #campi aggiuntivi
    published = fields.Boolean(string="Visibile sul Sito?",default="True")
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
    qty_available_now = fields.Integer(string="Quantità Disponibile",compute="_get_qty_available_now",
        help="Quantità Disponibile Adesso (qty in possesso - qty in uscita)")
    qty_sum_suppliers = fields.Integer(string="Quantità dei fornitori", compute="_get_qty_suppliers",
        help="Somma delle quantità dei fornitori")

    #override per calcolare meglio gli acquisti
    purchase_count = fields.Integer(string="Acquisti", compute="_get_sum_purchases",
        help="Acquisti")
    sales_count = fields.Integer(string="Vendite", compute="_get_sum_sales",
        help="Vendite")

    #separo la descrizione e il nome
    description = fields.Html(string="Descrizione")

    bom_count = fields.Integer(compute="_get_sum_bom")

    @api.one
    def _get_sum_bom(self):
        attr = [('product_id','=',self.id)]
        results = self.env['mrp.bom'].search_count(attr)
        self.bom_count=results

    @api.one
    def _get_sum_sales(self):
        attr = [('product_id','=',self.id)]
        results = self.env['sale.order.line'].search_count(attr)
        self.sales_count=results

    @api.one
    def _get_sum_purchases(self):
        attr = [('product_id','=',self.id)]
        results = self.env['purchase.order.line'].search_count(attr)
        self.purchase_count=results

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

                detax = final / (float(1) + float(tassa/100))

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

            detax = values['final_price'] / (float(1) + float(tassa/100))
            deiva = round(detax,2)
            values['list_price'] = deiva

        return  super(Products, self).create(values)

    @api.one
    def toggle_published(self):
        value = not self.published
        attr = {'published':value}
        self.write(attr)

    def _check_attribute_value_ids(self, cr, uid, ids, context=None):
        
        return True

    _constraints = [
        (_check_attribute_value_ids, 'Override', ['attribute_value_ids'])
    ]

class Template(models.Model):
    _inherit = 'product.template'

    #campi override per rendere le varianti indipendenti dai template
    lst_price = fields.Float(string="Prezzo senza Iva")
    list_price = fields.Float(string="Prezzo Listino")

    #campi aggiunti
    published = fields.Boolean(string="Visibile sul Sito?",default="True")
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

    #campi aggiunti per visualizzare anche le varianti con active=False
    #da problemi con la funzione _compute_product_template_field in addons/product/product.py
    #per questo motivo metto un altro conteggio in un altro campo
    product_variant_count_bis = fields.Integer(compute="_get_count_variants")

    #separo la descrizione e il nome
    description = fields.Html(string="Descrizione")

    @api.model
    def create(self,values):
        """
        questi sono alcuni campi separati che 'potrebbero' essere uguali tra
        template e varianti (sono comunque modificabili singolarmente)
        """
        new_id = super(Template, self).create(values)

        attr={k: v for k, v in values.items() if k in ['out_date','out_date_approx_type','active','published','description']}

        new_id.product_variant_ids.write(attr)

        return new_id

    @api.multi
    def write(self,values):

        attr={k: v for k, v in values.items() if k in ['out_date','out_date_approx_type','active','published','description']}

        self.product_variant_ids.write(attr)

        return super(Template, self).write(values)

    @api.one
    def _get_count_variants(self):
        """
        sovrascrivo il campo product_variant_count per contare anche i prodotti non attivi
        """
        searched = [('product_tmpl_id','=',self.id),'|',('active','=',False),('active','=',True)]
        result = self.env['product.product'].search(searched)
        self.product_variant_count_bis = len(result)

    @api.one
    def toggle_published(self):
        value = not self.published
        attr = {'published':value}
        self.write(attr)

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    #campi aggiunti
    avail_qty = fields.Float('Quantità disponibile',
        help="Il valore 0 non indica necessariamente l'assenza di disponibilità")

    #uso le nuove api perchè sono più figo
    @api.model
    def create(self,values):
        """
        cerco il variant attuale,
        mi prendo il template e correggo
        """
        if 'product_id' in values.keys():
            obj = self.env['product.product'].search([('id','=',values['product_id'])])
            templ = obj.product_tmpl_id.id
            values['product_tmpl_id']=templ

        return super(SupplierInfo, self).create(values)