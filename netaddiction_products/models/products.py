# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools
from openerp.osv import fields as old_fields
import openerp.addons.decimal_precision as dp
import datetime

class Products(models.Model):
    _inherit = 'product.product'

    #separazione listini di acquisto
    seller_ids = fields.One2many('product.supplierinfo', 'product_id', 'Supplier')
    #separazione prezzo di  vendita e creazione prezzo ivato e senza iva
    lst_price = fields.Float(string="Prezzo di Vendita", digits_compute= dp.get_precision('Product Price'))
    #list_price = fields.Float(string="Prezzo di vendita Iva Esclusa", compute="_get_price", digits_compute= dp.get_precision('Product Price'))
    #MOD TASSE
    list_price = fields.Float(string="Prezzo di vendita", compute="_get_price", digits_compute= dp.get_precision('Product Price'))

    #CAMPI DI VISTA
    detax_price = fields.Float(string="Prezzo di vendita deivato" ,compute = "_get_visual_price", digits_compute= dp.get_precision('Product Price'))
    intax_price = fields.Float(string="Prezzo di vendita Ivato", compute = "_get_visual_price", digits_compute= dp.get_precision('Product Price'))

    #campo prezzo ivato
    final_price = fields.Float(string="Prezzo Listino", digits_compute= dp.get_precision('Product Price'))
    special_price = fields.Float(string="Prezzo offerta base", digits_compute=dp.get_precision('Product Price'), default=0)
    
    #campi aggiuntivi
    sale_ok = fields.Boolean(string="Vendibile",default="True")

    visible = fields.Boolean(string="Visibile",default="True")

    alias_ids = fields.One2many('netaddiction_products.alias', 'product_id')

    out_date = fields.Date(string="Data di Uscita")
    out_date_approx_type = fields.Selection(string="Approssimazione Data",
        selection=(('accurate','Preciso'),('month','Mensile'),('quarter','Trimestrale'),
        ('four','Quadrimestrale'),('year','Annuale'),('nothing','Nessuna')),
        help="""Impatta sulla vista front end,
        Preciso: la data inserita è quella di uscita,
        Mensile: qualsiasi data inserita prende solo il mese e l'anno (es: in uscita nel mese di Dicembre 2019),
        Trimestrale: prende l'anno e mese e calcola il trimestre(es:in uscita nel terzo trimestre 2019),
        Quadrimestrale: prende anno e mese e calcola il quadrimestre(es:in uscita nel primo quadrimestre del 2019),
        Annuale: prende solo l'anno (es: in uscita nel 2019)
        Nessuna: quando non esiste la data di uscita""" )

    available_date = fields.Date(string="Data disponibilità")

    qty_available_now = fields.Integer(string="Quantità Disponibile",compute="_get_qty_available_now",
        help="Quantità Disponibile Adesso (qty in possesso - qty in uscita)",search="_search_available_now")
    qty_sum_suppliers = fields.Integer(string="Quantità dei fornitori", compute="_get_qty_suppliers",
        help="Somma delle quantità dei fornitori")

    qty_single_order = fields.Integer(string="Quantità massima ordinabile" , help="Quantità massima ordinabile per singolo ordine/cliente")

    image_ids = fields.Many2many('ir.attachment', 'product_image_rel', 'product_id', 'attachment_id', string='Immagini')

    qty_limit = fields.Integer(string="Quantità limite", help="Imposta la quantità limite prodotto (qty disponibile == qty_limit accade Azione)")
    limit_action = fields.Selection(string="Azione limite", help="Se qty_limit impostata decide cosa fare al raggiungimento di tale qty",
            selection= (('nothing','Nessuna Azione'),('no_purchasable','Non vendibile'),('deactive','Invisibile e non vendibile')))

    #override per calcolare meglio gli acquisti
    purchase_count = fields.Integer(string="Acquisti", compute="_get_sum_purchases",
        help="Acquisti")
    sales_count = fields.Integer(string="Vendite", compute="_get_sum_sales",
        help="Vendite")

    #separo la descrizione e il nome
    description = fields.Html(string="Descrizione")

    bom_count = fields.Integer(compute="_get_sum_bom")

    property_cost_method = fields.Selection(selection=[('standard', 'Standard Price'),
                       ('average', 'Average Price'),
                       ('real', 'Real Price')], string="Metodo Determinazioni costi", default="real", required=1)
    property_valuation = fields.Selection( selection=[('manual_periodic', 'Periodic (manual)'),
                       ('real_time', 'Perpetual (automated)')], string="Valorizzazione Inventario", default="real_time", required=1)

    _columns = {
        'image': old_fields.binary("Image", attachment=True,
            help="This field holds the image used as image for the product, limited to 1024x1024px."),
        'image_medium': old_fields.binary("Image", attachment=True,
            help="Medium-sized image of the product. It is automatically resized as a 128x128px image, with aspect ratio preserved, "\
                 "only when the image exceeds one of those sizes. Use this field in form views or some kanban views."),
        'image_small': old_fields.binary("Image", attachment=True,
            help="Small-sized image of the product. It is automatically resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
    }

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

    def _search_available_now(self, operator, value):
        ids = []
        wh = self.env['stock.location'].search([('company_id','=',self.env.user.company_id.id),('active','=',True),
            ('usage','=','internal'),('scrap_location','=',False)])

        search = [('location_id','=',wh.id),('reservation_id','=',False)]

        domain_for_zero = [('state', 'not in', ('done', 'cancel', 'draft')), ('company_id', '=', self.env.user.company_id.id)]

        if operator == '<' or operator == '<=' or operator == '=':
            moves_out = self.env['stock.move'].read_group(domain = domain_for_zero, fields = ['product_id','product_qty'], groupby = 'product_id')

            for move in moves_out:
                pid = self.env['product.product'].search([('id','=',int(move['product_id'][0]))])
                if operator == '<' and pid.qty_available_now < value:
                    ids.append(pid.id)
                if operator == '<=' and pid.qty_available_now <= value:
                    ids.append(pid.id)
                if operator == '=' and pid.qty_available_now == value:
                    ids.append(pid.id)


        if operator == '>':
            self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) > %s", (wh.id,self.env.user.company_id.id,value))
        if operator == '>=':
            self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) >= %s", (wh.id,self.env.user.company_id.id,value))
        if operator == '=':
            if value == 0:
                products = self.env['product.product'].search([('qty_available','=',0),('company_id','=',self.env.user.company_id.id)])
                for pid in products:
                    if operator == '<' and pid.qty_available_now < value:
                        ids.append(pid.id)
                    if operator == '<=' and pid.qty_available_now <= value:
                        ids.append(pid.id)
                    if operator == '=' and pid.qty_available_now == value:
                        ids.append(pid.id)

            self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) = %s", (wh.id,self.env.user.company_id.id,value))
        if operator == '<':
            self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id  having sum(qty) < %s", (wh.id,self.env.user.company_id.id,value))
        if operator == '<=':
            self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) <= %s", (wh.id,self.env.user.company_id.id,value))

        quants = self.env.cr.fetchall()
        for quant in quants:
            ids.append(quant[0])

        return [('id','in',ids)]

    @api.one
    def _get_qty_suppliers(self):
        """
        somma, se ci sono, tutte le quantità dei fornitori
        """
        qty = 0
        for sup in self.seller_ids:
            qty = qty + int(sup.avail_qty)
        self.qty_sum_suppliers = qty

    @api.depends('final_price','special_price')
    def _get_price(self):

        for p in self:
            tassa = p.taxes_id
        
            if p.special_price > 0.00:
                price = p.special_price
            else:
                price = p.final_price

            p.list_price = price

    @api.depends('final_price','special_price')
    def _get_visual_price(self):
        for p in self:
            result = p.taxes_id.compute_all(p.list_price)
        
            p.detax_price = result['total_excluded']
            p.intax_price = result['total_included']

    def create(self, cr, uid, vals, context=None):
        try:
            tools.image_resize_images(vals)
        except IOError:
            if not context.get('skip_broken_images', False):
                raise
        return super(Products, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        try:
            tools.image_resize_images(vals)
        except IOError:
            if not context.get('skip_broken_images', False):
                raise
        product = self.browse(cr,uid,ids)
        for pid in product:
            if not context.get('no_check_price_and_date', False):
                pid.check_price_and_date(vals)

        return super(Products, self).write(cr, uid, ids, vals, context)

    @api.one
    def check_price_and_date(self,vals):
        """
        quando cambia il prezzo del prodotto ed è minore di quello precedente ed il prodotto è in prenotazione
        deve andare a controllare negli ordini e cambiare il prezzo in questi ordini se il prezzo di questi ordini  maggiore
        del nuovo prezzo altrimenti lascia quello già presente
        """
        actual_price = self.list_price
        
        today = datetime.date.today()
        if self.out_date:
            out_date = datetime.datetime.strptime(self.out_date,'%Y-%m-%d').date()
            if out_date > today:
                special = False
                final = False
                if 'special_price' in vals.keys():
                    special = vals['special_price']
                if 'final_price' in vals.keys():
                    final = vals['final_price']
                price = 0
                if special:
                    price = special
                else:
                    price = final

                result_price = self.taxes_id.compute_all(price)
                price_new = result_price['total_included']

                result_list_price = self.taxes_id.compute_all(self.list_price)
                list_price = result_list_price['total_included']

                
                if price_new < list_price:
                    lines = self.env['sale.order.line'].search([('product_id','=',self.id),('order_id.state','!=','done')])
                    for line in lines:
                        res_price_unit = line.tax_id.compute_all(line.price_unit)
                        price_unit = res_price_unit['total_included']
                        if price_new < price_unit:
                            pre = line.order_id.amount_total
                            line.write({'price_unit' : price})
                            gift = pre - line.order_id.amount_total
                            line.order_id.partner_id.add_gift_value(gift,'Rimborso')

        if 'out_date' in vals:
            #qua significa che ho modificato la data di uscita
            old_out_date = datetime.datetime.strptime(self.out_date,'%Y-%m-%d').date()
            new_out_date = datetime.datetime.strptime(vals['out_date'],'%Y-%m-%d').date()

            if new_out_date != old_out_date and new_out_date > datetime.date.today():
                pick = self.env['stock.picking'].search([('move_lines.product_id','=',self.id)])
                pick.write({'min_date':new_out_date - datetime.timedelta(days = 1)})



            

    def get_actual_price(self):
        #return self.special_price if (self.special_price>0.00) else self.final_price
        #MOD TASSE
        return self.list_price

    @api.one
    def toggle_purchasable(self):
        self.sale_ok = not self.sale_ok

    @api.one
    def toggle_visible(self):
        value = not self.visible
        attr = {'visible':value}
        self.write(attr)

    @api.multi
    def manage_aliases(self):
        self.ensure_one()

        return {
            'name': 'Gestione alias di %s' % self.name,
            'view_type': 'form',
            'view_mode': 'list',
            'view_id': False,
            'res_model': 'netaddiction_products.alias',
            'type': 'ir.actions.act_window',
            'domain': [('product_id.id', '=', self.id)],
            'target': 'new',
            'flags': {
                'action_buttons': True,
                'pager': True,
            },
            'context': {
                'default_product_id': self.id,
            },
        }

    

    #uccido la constrains di un unico attributo per tipo
    def _check_attribute_value_ids(self, cr, uid, ids, context=None):
        
        return True

    _constraints = [
        (_check_attribute_value_ids, 'Override', ['attribute_value_ids'])
    ]

    


class Template(models.Model):
    _inherit = 'product.template'

    #campi override per rendere le varianti indipendenti dai template
    lst_price = fields.Float(string="Prezzo Listino")
    list_price = fields.Float(string="Prezzo Listino")

    #campi aggiunti
    sale_ok = fields.Boolean(string="Acquistabile",default="True")
    visible = fields.Boolean(string="Visibile",default="True")
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

    available_date = fields.Date(string="Data disponibilità")

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

        attr={k: v for k, v in values.items() if k in ['available_date','out_date','out_date_approx_type','active','sale_ok','description','visible']}

        new_id.product_variant_ids.write(attr)

        return new_id

    @api.multi
    def write(self,values):

        attr={k: v for k, v in values.items() if k in ['available_date','out_date','out_date_approx_type','active','sale_ok','description','visible']}

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
    def toggle_purchasable(self):
        self.sale_ok = not self.sale_ok

    @api.one
    def toggle_visible(self):
        value = not self.visible
        attr = {'visible':value}
        self.write(attr)


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    # Campi aggiunti
    avail_qty = fields.Float('Quantità disponibile',
        help="Il valore 0 non indica necessariamente l'assenza di disponibilità")

    _defaults = {
        'delay': None,
    }

    @api.model
    def create(self, values):
        # Cerco il variant attuale, mi prendo il template e correggo
        if 'product_id' in values.keys():
            obj = self.env['product.product'].search([('id', '=', values['product_id'])])
            templ = obj.product_tmpl_id.id
            values['product_tmpl_id'] = templ

        # Se non è specificato un tempo di consegna lo prendo dal fornitore associato
        if values.get('delay') is None:
            supplier = self.env['res.partner'].search([('id', '=', values['name'])])
            values['delay'] = supplier.supplier_delivery_time

        return super(SupplierInfo, self).create(values)

    @api.one
    @api.constrains('avail_qty')
    def auto_deactivate_products(self):
        """
        Attiva o disattiva il prodotto associato in base alla quantità di magazzino e del fornitore.
        """
        # IMPORTANTE: mantenere l'ordine e la sovrabbondanza di condizioni per ridurre al minimo la quantità di query
        if self.avail_qty > 0:
            if not self.product_id.sale_ok and \
                    self.product_id.categ_id.can_auto_deactivate_products:
                self.product_id.sale_ok = True

            if self.product_id.categ_id.auto_supplier_delay and \
                    self.delay != self.name.supplier_delivery_time:
                self.delay = self.name.supplier_delivery_time
        else:
            if self.product_id.sale_ok and \
                    self.product_id.categ_id.can_auto_deactivate_products and \
                    self.product_id.qty_sum_suppliers == 0 and \
                    self.product_id.qty_available_now == 0:
                self.product_id.sale_ok = False

            if self.product_id.categ_id.auto_supplier_delay and \
                    self.delay != self.product_id.categ_id.auto_supplier_delay:
                self.delay = self.product_id.categ_id.auto_supplier_delay


class Category(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one('res.company', required=True)
    can_auto_deactivate_products = fields.Boolean('Disattiva automaticamente i prodotti', default=False,
        help='I prodotti vengono disattivati non appena la disponibilità in magazzino e le disponibilità dei '
             'fornitori scendono a zero.')
    auto_supplier_delay = fields.Integer('Imposta automaticamente il tempo di consegna del fornitore', required=False, default=None,
        help='Quando la quantità del fornitore di un prodotto scende a zero, questo è il valore che assumerà il '
             'tempo di consegna. Il valore 0 verrà ignorato.')


class Attribute(models.Model):
    _inherit = 'product.attribute'

    company_id = fields.Many2one('res.company', required=True)


class AttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    company_id = fields.Many2one('res.company', related='attribute_id.company_id', store=True)


class Alias(models.Model):
    _name = 'netaddiction_products.alias'

    product_id = fields.Many2one('product.product', required=True)
    name = fields.Char('Nome')
