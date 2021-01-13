# -*- coding: utf-8 -*-
from io import StringIO
import base64
from odoo import models, fields, api
from collections import defaultdict
from datetime import datetime,date,timedelta


'''

# TODO: Porting if we need it

class ProductProduct(models.Model):

    _inherit = "product.product"


    @api.model
    def get_qty_available_negative(self,search,supplier_id = None, context=None):
        if not context:
            context = {}
        result = []
        if search:
            domain = [('company_id','=',self.env.user.company_id.id),('qty_available_now','<',0),('barcode','=',str(search))]
        else:
            domain = [('company_id','=',self.env.user.company_id.id),('qty_available_now','<',0)]

        if supplier_id and supplier_id != 'all':
            domain.append(('seller_ids.name','=',int(supplier_id)))

        products = self.search(domain)

        pids = []
        for prod in products:
            pids.append(prod.id)
            search = self.env['purchase.order.line'].search([('product_id','=',prod.id),('state','=','draft')])
            qty = 0
            purchases = ''
            for s in search:
                qty = qty + s.product_qty

            visible = 1
            if prod.qty_available - prod.outgoing_qty + prod.incoming_qty >= 0:
                #escludo i prodotti con prevista >= 0 (già ordinati)
                visible = 0

            if prod.out_date:
                if datetime.strptime(prod.out_date,'%Y-%m-%d') > datetime.now():
                    visible = 0

            attr = {
                'id' : prod.id,
                'display_name' : prod.with_context(context).display_name,
                'qty_available' : prod.qty_available,
                'qty_available_now' : prod.qty_available_now,
                'virtual_available' : prod.virtual_available,
                'outgoing_qty' : prod.outgoing_qty,
                'incoming_qty' : (int(prod.incoming_qty) + int(qty)),
                #'inorder_qty' : qty,
                'seller_ids' : [],
                'visible' : visible,
                'barcode' : prod.barcode,
                'category': prod.categ_id.id,
                'out_date':prod.out_date,
            }

            for sup in prod.seller_ids:
                if sup.name.active:
                    attr['seller_ids'].append({
                        'id' : sup.name.id,
                        'name' : sup.name.name,
                        'price' : sup.price,
                        'delay' : sup.delay,
                        'avail_qty' : sup.avail_qty,
                        'product_code' : sup.product_code
                        })
            result.append(attr)

        # qua cerco i prodotti solo in prenotazione
        preorders = self.search([('out_date', '>', date.today().strftime('%Y-%m-%d'))])
        for prod in preorders:
            if prod.id not in pids:
                search = self.env['purchase.order.line'].search([('product_id','=',prod.id),('state','=','draft')])
                qty = 0
                purchases = ''
                for s in search:
                    qty = qty + s.product_qty
                visible = 1
                if prod.qty_available - prod.outgoing_qty + prod.incoming_qty >= 0:
                    #escludo i prodotti con prevista >= 0 (già ordinati)
                    visible = 0
                
                if prod.out_date:
                    if datetime.strptime(prod.out_date,'%Y-%m-%d') > datetime.now():
                        visible = 0

                attr = {
                    'id' : prod.id,
                    'display_name' : prod.display_name,
                    'qty_available' : prod.qty_available,
                    'qty_available_now' : prod.qty_available_now,
                    'virtual_available' : prod.virtual_available,
                    'outgoing_qty' : prod.outgoing_qty,
                    'incoming_qty' : (int(prod.incoming_qty) + int(qty)),
                    #'inorder_qty' : qty,
                    'seller_ids' : [],
                    'visible' : visible,
                    'barcode' : prod.barcode,
                    'category': prod.categ_id.id,
                    'out_date':prod.out_date
                }

                for sup in prod.seller_ids:
                    if sup.name.active:
                        attr['seller_ids'].append({
                            'id' : sup.name.id,
                            'name' : sup.name.name,
                            'price' : sup.price,
                            'delay' : sup.delay,
                            'avail_qty' : sup.avail_qty,
                            'product_code' : sup.product_code
                            })
                result.append(attr)

        return result
'''


class PurchaseOrder(models.Model):

    _inherit="purchase.order"

    READONLY_STATES_NEW = {
        #'purchase': [('readonly', True)],
        #'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    order_line = fields.One2many(
        'purchase.order.line', 'order_id', string='Order Lines',
        states=READONLY_STATES_NEW,
        copy=True
    )

    @api.model
    def put_in_order(self, products):
        """
        products: lista di liste [product_id,supplier_id,qty _order]
        data la lista cerca se c'è già aperto un ordine per quel fornitore e inserisce la riga corrispondente,
        altrimenti crea il nuovo ordine
        """
        organize = {}
        for product in products:
            supplier_id = product[1]
            if supplier_id not in organize:
                organize.update({supplier_id: []})
            organize[supplier_id].append(product)

        for supplier, prods in organize.items():
            orders = self.search([
                ('company_id', '=', self.env.user.company_id.id),
                ('state', '=', 'draft'),
                ('partner_id', '=', int(supplier)),
                ])
            line_values = self._return_attr(prods,supplier)
            if not orders:
                attr = {
                    'partner_id': int(supplier),
                    'order_line': line_values
                }
                self.env['purchase.order'].create(attr)
            else:
                orders[0].write({'order_line': line_values})
        return True

    def _return_attr(self, prods, supplier):
        line_values = []
        for p in prods:
            prod = self.env['product.product'].search([('id','=',int(p[0]))])
            price_unit = 0.0
            name = ''
            delay = 1
            for i in prod.seller_ids:
                if i.name.id == int(supplier):
                    price_unit = i.price
                    name = i.product_name or prod.display_name
                    delay = i.delay
                    attr = {
                        'product_id': int(p[0]),
                        'product_qty': int(p[2]),
                        'product_uom': prod.uom_po_id.id or prod.uom_id.id,
                        'price_unit': float(price_unit),
                        'name': name,
                        'date_planned': datetime.now() + timedelta(
                            days=int(delay)),
                        }
                    if prod.supplier_taxes_id:
                        attrs['taxes_id'] = [
                            (6, False, [prod.supplier_taxes_id.id])]
                    line_values.append((0,0,attr))
        return line_values

    def action_rfq_send(self):
        # Ignore standard return (the send mail wizard)
        # but call `super` to keep the stack alive
        super().action_rfq_send()
        user = self.env.user
        template = self.env.ref(
            'netaddiction_purchase_orders.netaddiction_purchase')
        template = template.sudo().with_context(lang=user.lang)
        attachment_name = 'ord_tvideo.txt'
        mail_model = self.env['mail.mail']
        attachment_model = self.env['ir.attachment']
        for purchase in self:
            # `force_send` MUST BE ALWAYS False or attachments don't work
            mail_id = template.send_mail(
                purchase.id, force_send=False, raise_exception=True)
            # If partner need terminalvideo report, generate attachment
            if purchase.partner_id.\
                    send_contact_purchase_orders_type == 'terminalvideo':
                mail = mail_model.browse(mail_id)
                file_content = '\r\n'.join(
                    [f'{l.product_id.barcode};'
                     f'{int(l.product_qty)};'
                     f'{l.price_unit}'
                     for l in purchase.order_line]
                    )
                file = StringIO()
                file.write(file_content)
                data_attach = {
                    'type': 'binary',
                    'name': attachment_name,
                    'datas': base64.b64encode(file.getvalue().encode('ascii')),
                    'description': attachment_name,
                }
                attachment = attachment_model.create(data_attach)
                mail.attachment_ids = attachment
        # Bypass standard return
        return {}


'''

# TODO: Porting if we need it

class ProductCategory(models.Model):

    _inherit = "product.category"

    @api.model
    def get_all_categories(self):
        result = self.sudo().search([])
        categories = []
        for res in result:
            categories.append({'id':res.id, 'name':res.name})
        return categories
'''
