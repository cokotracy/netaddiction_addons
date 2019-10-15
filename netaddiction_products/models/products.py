# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools, SUPERUSER_ID
from openerp.osv import fields as old_fields
import openerp.addons.decimal_precision as dp
import datetime
from openerp.tools.float_utils import float_round

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

    qty_available_now = fields.Integer(string="Quantità Disponibile", compute="_get_qty_available_now", help="Quantità Disponibile Adesso (qty in possesso - qty in uscita)", search="_search_available_now")
    qty_sum_suppliers = fields.Integer(string="Quantità dei fornitori", compute="_get_qty_suppliers",
        help="Somma delle quantità dei fornitori")

    qty_single_order = fields.Integer(string="Quantità massima ordinabile", help="Quantità massima ordinabile per singolo ordine/cliente")

    image_ids = fields.Many2many('ir.attachment', 'product_image_rel', 'product_id', 'attachment_id', string='Immagini')
    video_ids = fields.One2many('netaddiction_products.video', 'product_id', string='Video')

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

    med_inventory_value = fields.Float(string="Valore Medio Inventario Deivato", default=0, compute="_get_inventory_medium_value")
    med_inventory_value_intax = fields.Float(string="Valore Medio Inventario Ivato", default=0, compute="_get_inventory_medium_value")

    @api.one
    def _get_inventory_medium_value(self):
        stock = self.env.ref('stock.stock_location_stock').id
        if self.qty_available > 0:
            quants = self.env['stock.quant'].search([('product_id', '=', self.id), ('location_id', '=', stock), ('company_id', '=', self.env.user.company_id.id)])
            qta = 0
            value = 0
            for quant in quants:
                qta += quant.qty
                value += quant.inventory_value
            val = float(value) / float(qta)
            result = self.supplier_taxes_id.compute_all(val)
            self.med_inventory_value_intax = round(result['total_included'], 2)
            self.med_inventory_value = round(result['total_excluded'], 2)
        else:
            self.med_inventory_value = 0

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        return super(Products, self)._product_available(cr, uid, ids, field_names, arg, context)
        context = context or {}
        field_names = field_names or []

        domain_products = [('product_id', 'in', ids)]
        domain_quant, domain_move_in, domain_move_out = [], [], []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(cr, uid, ids, context=context)
        domain_move_in += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_move_out += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_quant += domain_products

        if context.get('lot_id'):
            domain_quant.append(('lot_id', '=', context['lot_id']))
        if context.get('owner_id'):
            domain_quant.append(('owner_id', '=', context['owner_id']))
            owner_domain = ('restrict_partner_id', '=', context['owner_id'])
            domain_move_in.append(owner_domain)
            domain_move_out.append(owner_domain)
        if context.get('package_id'):
            domain_quant.append(('package_id', '=', context['package_id']))

        domain_move_in += domain_move_in_loc
        domain_move_out += domain_move_out_loc
        moves_in = self.pool.get('stock.move').read_group(cr, uid, domain_move_in, ['product_id', 'product_qty'], ['product_id'], context=context)
        moves_out = self.pool.get('stock.move').read_group(cr, uid, domain_move_out, ['product_id', 'product_qty'], ['product_id'], context=context)

        domain_quant += domain_quant_loc
        quants = self.pool.get('stock.quant').read_group(cr, uid, domain_quant, ['product_id', 'qty'], ['product_id'], context=context)
        quants = dict(map(lambda x: (x['product_id'][0], x['qty']), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))
        res = {}
        ctx = context.copy()
        ctx.update({'prefetch_fields': False})
        for product in self.browse(cr, uid, ids, context=ctx):
            id = product.id
            qty_available = float_round(quants.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            incoming_qty = float_round(moves_in.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            outgoing_qty = float_round(moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            virtual_available = float_round(quants.get(id, 0.0) + moves_in.get(id, 0.0) - moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            res[id] = {
                'qty_available': qty_available,
                'incoming_qty': incoming_qty,
                'outgoing_qty': outgoing_qty,
                'virtual_available': virtual_available,
            }
        return res

    def _new_search_qty_available(self, cr, uid, obj, name, domain, context):
        return self.pool.get('product.product').new_api_search_qty_available(cr, uid, domain, context=context)

    @api.model
    def new_api_search_qty_available(self, domain):
        # ricerca per qty_available
        # ritorna un dominio
        # TODO: migliora per uguale o diverso e semmai rinomi qty_available come field con la nuova search_func togliendo il sopra.
        wh_stock = self.env.ref('stock.stock_location_stock').id
        pids = []
        for field, operator, value in domain:
            assert operator in ('<', '>', '=', '!=', '<=', '>='), 'Invalid domain operator'
            assert isinstance(value, (float, int)), 'Invalid domain right operand'

            if value == 0:
                if operator == '>=':
                    return []
                if operator == '<':
                    return [('id', '=', False)]

                self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) > %s", (wh_stock, self.env.user.company_id.id, 0))
                results = self.env.cr.fetchall()
                for res in results:
                    pids.append(int(res[0]))

                if operator in ('=', '<='):
                    return [('id', 'not in', pids)]

            if operator in ('=', '!='):
                self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) = %s", (wh_stock, self.env.user.company_id.id, value))
                results = self.env.cr.fetchall()
                for res in results:
                    pids.append(int(res[0]))
            if operator in ('>', '<='):
                self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) > %s", (wh_stock, self.env.user.company_id.id, value))
                results = self.env.cr.fetchall()
                for res in results:
                    pids.append(int(res[0]))
            if operator in ('>=', '<'):
                self.env.cr.execute("select product_id,sum(qty) from stock_quant where location_id = %s and reservation_id is Null and company_id = %s group by product_id having sum(qty) >= %s", (wh_stock, self.env.user.company_id.id, value))
                results = self.env.cr.fetchall()
                for res in results:
                    pids.append(int(res[0]))

        if operator in ('=', '>', '>='):
            return [('id', 'in', pids)]
        if operator in ('!=', '<', '<='):
            return [('id', 'not in', pids)]

    _columns = {
        'image': old_fields.binary("Image", attachment=True,
            help="This field holds the image used as image for the product, limited to 1024x1024px."),
        'image_medium': old_fields.binary("Image", attachment=True,
            help="Medium-sized image of the product. It is automatically resized as a 128x128px image, with aspect ratio preserved, "\
                 "only when the image exceeds one of those sizes. Use this field in form views or some kanban views."),
        'image_small': old_fields.binary("Image", attachment=True,
            help="Small-sized image of the product. It is automatically resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        'qty_available': old_fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Quantity On Hand',
            fnct_search=_new_search_qty_available,
            help="Current quantity of products.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
    }
    
    @api.one
    def _get_sum_bom(self):
        attr = [('product_id','=',self.id)]
        results = self.env['mrp.bom'].search_count(attr)
        self.bom_count=results

    @api.one
    def _get_sum_sales(self):
        lines = self.env['sale.order.line'].search([('product_id', '=', self.id), ('state', 'not in', ['cancel', 'draft', 'pending'])])
        count = 0
        for line in lines:
            count += line.product_qty - line.qty_reverse
        self.sales_count = count

    @api.one
    def _get_sum_purchases(self):
        attr = [('product_id', '=', self.id)]
        results = self.env['purchase.order.line'].search(attr)
        count = 0
        for line in results:
            count += line.product_qty
        self.purchase_count = count

    @api.one
    def _get_qty_available_now(self):
        self.qty_available_now = int(self.qty_available) - int(self.outgoing_qty)

    def _search_available_now(self, operator, value):
        domain = []
        ids = []
        domain_for_zero = [('state', 'not in', ('done', 'cancel', 'draft')), ('company_id', '=', self.env.user.company_id.id)]
        moves_out = self.env['stock.move'].read_group(domain=domain_for_zero, fields=['product_id', 'product_qty'], groupby='product_id')
        product_ids = [prod['product_id'][0] for prod in moves_out]
        products = self.env['product.product'].search([('id', 'in', product_ids)])
        for prod in products:
            qty_available_now = prod.qty_available_now
            if operator == '<=' and qty_available_now <= value:
                ids.append(prod.id)
            if operator == '<' and qty_available_now < value:
                ids.append(prod.id)
            if operator == '>=' and qty_available_now < value:
                ids.append(prod.id)
            if operator == '>' and qty_available_now <= value:
                ids.append(prod.id)
            if operator == '=' and value >= 0 and qty_available_now != value:
                ids.append(prod.id)
            if operator == '=' and value < 0 and qty_available_now == value:
                ids.append(prod.id)

        # caso in cui value è zero
        if value == 0 and operator == '<=':
            domain = ['|', ('qty_available', '<=', 0), ('id', 'in', ids)]
        if value == 0 and operator == '<':
            domain = [('id', 'in', ids)]
        if value == 0 and operator == '>=':
            available = self.env['product.product'].search([('qty_available', '>=', 0)])
            t = [item for item in available.ids if item not in ids]
            domain = [('id', 'in', t)]
        if value == 0 and operator == '>':
            available = self.env['product.product'].search([('qty_available', '>', 0)])
            t = [item for item in available.ids if item not in ids]
            domain = [('id', 'in', t)]
        if value == 0 and operator == '=':
            available = self.env['product.product'].search([('qty_available', '=', 0)])
            t = [item for item in available.ids if item not in ids]
            domain = [('id', 'in', t)]

        # caso in cui value è > 0
        if value > 0 and (operator == '<=' or operator == '<'):
            domain = ['|', ('qty_available', operator, value), ('id', 'in', ids)]
        if value > 0 and (operator == '>=' or operator == '>'):
            available = self.env['product.product'].search([('qty_available', operator, value)])
            t = [item for item in available.ids if item not in ids]
            domain = [('id', 'in', t)]
        if value > 0 and operator == '=':
            available = self.env['product.product'].search([('qty_available', '=', value)])
            t = [item for item in available.ids if item not in ids]
            domain = [('id', 'in', t)]

        # caso in cui value è < 0
        if value < 0 and (operator == '<=' or operator == '<'):
            domain = [('id', 'in', ids)]
        if value < 0 and (operator == '>=' or operator == '>'):
            available = self.env['product.product'].search([('qty_available', operator, value)])
            t = [item for item in available.ids if item not in ids]
            domain = [('id', 'in', t)]
        if value < 0 and operator == '=':
            domain = [('id', 'in', ids)]

        return domain

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

        if 'barcode' in vals:
            # Se il barcode è un UPC-A lo converto in EAN-13
            if self.pool['barcode.nomenclature'].check_encoding(vals['barcode'], 'upca'):
                vals['barcode'] = '0' + vals['barcode']

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
            if self.out_date:
                old_out_date = datetime.datetime.strptime(self.out_date,'%Y-%m-%d').date()
            else:
                old_out_date = datetime.date.today()

            new_out_date = datetime.datetime.strptime(vals['out_date'],'%Y-%m-%d').date()

            if new_out_date != old_out_date and new_out_date > datetime.date.today():
                pick = self.env['stock.picking'].search([('move_lines.product_id','=',self.id)])
                pick.write({'min_date':new_out_date - datetime.timedelta(days = 1)})
    

    @api.constrains('available_date')
    def available_date_change(self):
        # cerco tutte le spedizioni che sono 'confirmed' [attesa disponibilita]
        # con questo prodotto 
        picks = self.env['stock.picking'].search([('move_lines.product_id','=',self.id),('state','=','confirmed'),('min_date','<',self.available_date)])
        for pick in picks:
            pick.min_date = self.available_date

    @api.constrains('out_date')
    def out_date_change(self):
        # cerco tutte le spedizioni che sono 'confirmed' [attesa disponibilita]
        # con questo prodotto 
        picks = self.env['stock.picking'].search([('move_lines.product_id','=',self.id),('state','=','confirmed'),('min_date','<',self.out_date)])
        for pick in picks:
            pick.min_date = self.out_date

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
    

    @api.multi 
    def check_quantity_product(self,qty_ordered):
        """
        serve a fare i controlli sulla quantità ordinata
        qty_ordered è la quantità totale nell'ordine/carrello
        """
        self.ensure_one()
        qty_limit = self.qty_limit
        qty_single = self.qty_single_order
        action = self.limit_action
        if not action:
            action = 'nothing'
        #controllo quantità massima ordinabile per singolo ordine
        if self.type != 'service':
            if qty_single > 0:
                if qty_ordered > qty_single:
                    message = "Non puoi ordinare piu di %s pezzi per %s " % (qty_single,self.display_name)
                    raise ProductOrderQuantityExceededException(self.id,qty_single,message)
        
        if action != 'nothing' and self.type != 'service':
            #controllo che non vada sotto la quantità limite
            qty_residual = self.qty_available_now - qty_limit

            if self.categ_id.can_auto_deactivate_products:
                if qty_ordered > qty_residual:
                    if qty_residual > 0:
                        message = "Non puoi ordinare piu di %s pezzi per %s " % (qty_residual, self.display_name)
                    else:
                        message = u"%s è esaurito" % self.display_name
                    raise ProductOrderQuantityExceededLimitException(self.id,qty_residual,message)


    def name_get(self, cr, user, ids, context=None):
        """
        Ridefinisce il metodo per scartare alcune query inutili.
        """
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []

        def _name_get(d):
            name = d.get('name', '')
            code = context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code, name)
            return (d['id'], name)

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights(cr, user, "read")
        self.check_access_rule(cr, user, ids, "read", context=context)

        result = []
        for product in self.browse(cr, SUPERUSER_ID, ids, context=context):
            variant = ", ".join([v.name for v in product.attribute_value_ids])
            name = variant and "%s (%s)" % (product.name, variant) or product.name
            mydict = {
                'id': product.id,
                'name': name,
                'default_code': product.default_code,
            }
            result.append(_name_get(mydict))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=6):
        result = []
        zerofill = name
        if name:
            try:
                name = int(name)
            except ValueError:
                pass
            else:
                result = self.search([('id', '=', int(name))] + args)
                if result:
                    return result.name_get()
                    
            result = self.search([('barcode','=',zerofill)] + args)
            if result:
                return result.name_get()

            result = self.search([('seller_ids.product_code','=',zerofill)] + args)
            if result:
                return result.name_get()
 
            result = self.search([('name', 'ilike', zerofill)] + args, limit=limit)
            if result:
                return result.name_get()

        return False

    @api.model
    def _check_products_to_turn_off(self):
        # prendo i prodotti vendibili ma con quantità disponibile <=0
        prods = self.env["product.product"].search([("sale_ok", "=", True), ("qty_available_now", "<=", 0)])
        today = datetime.datetime.today()
        for prod in prods:
            # spengo i prodotti che non hanno i fornitori e che non sono prenotazioni (NB i prodotti senza outdate non contano come prenotazioni)
            if (prod.qty_sum_suppliers <= 0 and (not prod.out_date or (prod.out_date and (datetime.datetime.strptime(prod.out_date, "%Y-%m-%d") < today)))):
                prod.sale_ok = False


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
        return new_id

    @api.multi
    def write(self,values):

        res = super(Template, self).write(values)

        return res

    def create_variant_ids(self, cr, uid, ids, context=None):
        #bypass la creazione delle varianti e il misterioso bottone attiva
        #ora no nfa nulla ed è meglio così
        pass

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
    _order = 'sequence'

    # Campi aggiunti
    avail_qty = fields.Float('Quantità disponibile',
        help="Il valore 0 non indica necessariamente l'assenza di disponibilità")

    _defaults = {
        'delay': None,
    }

    detax_margin = fields.Float(string="Margine iva esclusa",compute="_calculate_margin_info")

    @api.one 
    def _calculate_margin_info(self):
        sup_price = self.product_id.supplier_taxes_id.compute_all(self.price)
        sale_price = self.product_id.offer_price if self.product_id.offer_price else self.product_id.list_price
        product_price = self.product_id.taxes_id.compute_all(sale_price)

        self.detax_margin = product_price['total_excluded'] - sup_price['total_excluded']

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
                if not self.product_id.active:
                    self.product_id.active = True

            if self.product_id.categ_id.auto_supplier_delay and \
                    self.delay != self.name.supplier_delivery_time:
                self.delay = self.name.supplier_delivery_time
        else:
            today = fields.Date.today()

            if self.product_id.sale_ok and \
                    self.product_id.categ_id.can_auto_deactivate_products and \
                    self.product_id.qty_sum_suppliers <= 0 and \
                    self.product_id.qty_available_now <= 0 and \
                    self.product_id.available_date <= today and \
                    self.product_id.out_date <= today:
                self.product_id.sale_ok = False

            if self.product_id.categ_id.auto_supplier_delay and \
                    self.delay != self.product_id.categ_id.auto_supplier_delay:
                self.delay = self.product_id.categ_id.auto_supplier_delay


class Category(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id)
    can_auto_deactivate_products = fields.Boolean('Disattiva automaticamente i prodotti', default=False,
        help='I prodotti vengono disattivati non appena la disponibilità in magazzino e le disponibilità dei '
             'fornitori scendono a zero.')
    auto_supplier_delay = fields.Integer('Imposta automaticamente il tempo di consegna del fornitore', required=False, default=None,
        help='Quando la quantità del fornitore di un prodotto scende a zero, questo è il valore che assumerà il '
             'tempo di consegna. Il valore 0 verrà ignorato.')


class Attribute(models.Model):
    _inherit = 'product.attribute'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id)


class AttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    company_id = fields.Many2one('res.company', related='attribute_id.company_id', store=True)


class Alias(models.Model):
    _name = 'netaddiction_products.alias'

    product_id = fields.Many2one('product.product', required=True)
    name = fields.Char('Nome')


class Video(models.Model):
    _name = 'netaddiction_products.video'

    product_id = fields.Many2one('product.product', required=True)
    embed = fields.Char('Embed')


class ProductOrderQuantityExceededException(Exception):
    def __init__(self, product_id, remains_quantity, err_str):
        super(ProductOrderQuantityExceededException, self).__init__(product_id)
        self.var_name = 'confirm_exception_product'
        self.err_str = err_str
        self.product_id = product_id
        self.remains_quantity = remains_quantity

        
    def __str__(self):
        s = u"Errore prodotto %s : %s " %(self.product_id, self.err_str)
        return s
    def __repr__(self):
        s = u"Errore prodotto %s : %s " %(self.product_id, self.err_str)
        return s

class ProductOrderQuantityExceededLimitException(Exception):
    def __init__(self, product_id, remains_quantity, err_str):
        super(ProductOrderQuantityExceededLimitException, self).__init__(err_str)
        self.var_name = 'confirm_exception_product_limit'
        self.err_str = err_str
        self.product_id = product_id
        self.remains_quantity = remains_quantity

        
    def __str__(self):
        s = u"Errore prodotto %s : %s " %(self.product_id, self.err_str)
        return s
    def __repr__(self):
        s = u"Errore prodotto %s : %s " %(self.product_id, self.err_str)
        return s