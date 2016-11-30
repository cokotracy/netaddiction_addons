# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import float_compare, float_round
import openerp.addons.decimal_precision as dp
import datetime
from calendar import monthrange

class AccountPicking(models.Model):
    _inherit = "stock.picking"
    
    @api.model
    def get_picking_from_data(self,year,month):
        tax_inc = self.env['account.tax'].search([('description','=','4v INC')])
        out_type = self.env.ref('stock.picking_type_out').id 
        refund_type = self.env['stock.picking.type'].search([('name','=','Reso Rivendibile')]).id 
        scraped_type = self.env['stock.picking.type'].search([('name','=','Reso Difettati')]).id 

        date_from = '%s-%s-01 00:00:00' % (year,month)
        last = monthrange(year, month)
        date_to = '%s-%s-%s 23:59:59' % (year,month,last[1])
        pickings = self.search([('date_done','>=',date_from),('date_done','<=',date_to),('picking_type_id','in',[out_type]),('state','=','done')])
        results = {'done':[],'refund':[]}
        ref_pid = {}
        for pick in pickings:
            for proc in pick.group_id.procurement_ids:
                variant = ", ".join([v.name for v in proc.sale_line_id.product_id.attribute_value_ids])
                attr = {
                        'product_id':proc.sale_line_id.product_id.name_template + ' (' + variant + ')',
                        'categ': proc.sale_line_id.product_id.categ_id.name,
                        'pid':proc.sale_line_id.product_id.id,
                        'barcode':proc.sale_line_id.product_id.barcode,
                        'qty':proc.sale_line_id.product_uom_qty,
                        'total_price':proc.sale_line_id.price_total,
                        'price_tax':proc.sale_line_id.price_tax,
                        'picking_id':pick.name,
                        'date_done':pick.date_done,
                        'payment_method':pick.sale_order_payment_method.name,
                        'state':pick.state,
                        'picking_type_id':pick.picking_type_id.name,
                        'sale_id':pick.origin,
                        'tax_id': proc.sale_line_id.tax_id.name,
                        'edizioni': 0,
                        }
                for attribute in proc.sale_line_id.product_id.attribute_value_ids:
                    if 'Multiplayer.it Edizioni' in attribute.name:
                        tax_value = tax_inc.compute_all(proc.sale_line_id.price_total)
                        attr['edizioni'] += (tax_value['total_included'] - tax_value['total_excluded'])
                attr['edizioni'] = round(attr['edizioni'],2)
                attr['price_tax'] = round(attr['price_tax'],2)
                attr['total_price'] = round(attr['total_price'],2)
                results['done'].append(attr)

        refunds = self.search([('date_done','>=',date_from),('date_done','<=',date_to),('picking_type_id','in',[refund_type,scraped_type]),('state','=','done')])
        for pick in refunds:
            for line in pick.pack_operation_product_ids:
                variant = ", ".join([v.name for v in proc.sale_line_id.product_id.attribute_value_ids])
                attr = {
                        'product_id':line.product_id.name_template + ' (' + variant + ')',
                        'categ': line.product_id.categ_id.name,
                        'pid':line.product_id.id,
                        'barcode':line.product_id.barcode,
                        'qty':line.qty_done,
                        'picking_id':pick.name,
                        'date_done':pick.date_done,
                        'payment_method':pick.sale_order_payment_method.name,
                        'state':pick.state,
                        'picking_type_id':pick.picking_type_id.name,
                        'sale_id':pick.origin,
                        'edizioni': 0,
                        }
                #qua cerco il valore nell'ordine
                order = self.env['sale.order'].search([('name','=',pick.origin)])
                for pid in order.order_line:
                    if pid.product_id.id == line.product_id.id:
                        attr['total_price'] = pid.price_unit * line.qty_done
                        amount = pid.product_id.taxes_id.compute_all(attr['total_price'])
                        tax = amount['total_included'] - amount['total_excluded']
                        attr['price_tax'] = tax
                        attr['tax_id']= pid.tax_id.name
                        for attribute in pid.product_id.attribute_value_ids:
                            if 'Multiplayer.it Edizioni' in attribute.name:
                                tax_value = tax_inc.compute_all(attr['total_price'])
                                attr['edizioni'] += (tax_value['total_included'] - tax_value['total_excluded'])

                attr['edizioni'] = round(attr['edizioni'],2)
                attr['price_tax'] = round(attr['price_tax'],2)
                attr['total_price'] = round(attr['total_price'],2)
                results['refund'].append(attr)
        return results