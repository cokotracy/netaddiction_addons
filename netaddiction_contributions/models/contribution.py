# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp import exceptions
import datetime
from pprint import pprint
from openerp.exceptions import ValidationError

class Contribution(models.Model):
    _name = "netaddiction.contribution"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('account.account'))
    name = fields.Char(string="Nome",required=True)
    partner_id = fields.Many2one(string="Fornitore", comodel_name="res.partner", required=True)
    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    contribution_type = fields.Selection(string="Tipo", selection=[('revaluation','Rivalutazione'),
                                                                   ('ads','Contributo Pubblicitario'),
                                                                   ('valuexship','Valore per Venduto')
                                                                  ], required=True)
    value = fields.Float(string="Valore",required=True)
    qty = fields.Integer(string="Quantità prodotto")
    date_start = fields.Date(string="Data Inizio",default=datetime.date.today().strftime('%Y-%m-%d'))
    date_finish = fields.Date(string="Data Fine",default=datetime.date.today().strftime('%Y-%m-%d'))
    state = fields.Selection(string="Stato",selection=[
                                                       ('draft','Bozza'),
                                                       ('confirmed','Confermato'),
                                                       ('closed','Chiuso')
                                                      ],default="draft")

    move_to_contribution = fields.Many2many(string="Righe Contributi/Movimentazioni", comodel_name="netaddiction.move.contribution")
    order_to_contribution = fields.One2many(string="Righe Ordini/Movimentazioni", comodel_name="netaddiction.order.contribution", inverse_name="contribution_id")

    #controlli per valuexship
    confirmed_qty = fields.Integer(string="Quantità Contribuita", compute="_get_confirmed_qty")
    confirmed_value = fields.Float(string="Valore Contribuito", compute="_get_confirmed_qty")

    invoice_ids = fields.Many2many(string="Note di Credito/Fatture", comodel_name="account.invoice")

    invoice_state = fields.Char(string="Stato Fatture", compute="_get_invoice_state")

    @api.one
    def _get_invoice_state(self):
        states = {
            'draft' : 'Bozza',
            'open' : 'Aperta',
            'paid' : 'Pagata',
        }

        state = 'draft'

        for inv in self.invoice_ids:
            if inv.state == 'open':
                state = 'open'
                break
            elif inv.state == 'draft':
                state = 'draft'
                break
            else:
                state = 'paid'

        self.invoice_state = states[state]


    @api.one 
    def action_close(self):
        if self.contribution_type == 'valuexship':
            account_id = self.env['account.account'].search([('code','=',410100),('company_id','=',self.env.user.company_id.id)])
            journal = self.env['account.journal'].search([('type','=','purchase'),('company_id','=',self.env.user.company_id.id)])
            attr = {
                'partner_id' : self.partner_id.id,
                'type' : 'in_refund',
                'journal_id' : journal.id,
                'account_id' : account_id.id,
                'invoice_line_ids' :[(0,False,{
                    'product_id' : self.product_id.id,
                    'quantity' : self.confirmed_qty,
                    'price_unit' : self.value,
                    'name' : self.product_id.name,
                    'account_id' : account_id.id,
                    'invoice_line_tax_ids' : [(6,False,[self.product_id.taxes_id.id])]
                    })],
                'number' : 'Contributo %s' % self.name,
                'date_invoice' : datetime.datetime.now()
            }
            refund = self.env['account.invoice'].create(attr)
            self.invoice_ids = [(4,refund.id,False)]
        elif self.contribution_type == 'ads':
            product = self.env['product.product'].search([('name','ilike','Contributo')])
            account_id = self.env['account.account'].search([('code','=',410100),('company_id','=',self.env.user.company_id.id)])
            journal = self.env['account.journal'].search([('type','=','purchase'),('company_id','=',self.env.user.company_id.id)])
            attr = {
                'partner_id' : self.partner_id.id,
                'type' : 'in_refund',
                'journal_id' : journal.id,
                'account_id' : account_id.id,
                'invoice_line_ids' :[(0,False,{
                    'product_id' : product.id,
                    'quantity' : 1,
                    'price_unit' : self.value,
                    'name' : 'Contributo %s' % self.name,
                    'account_id' : account_id.id,
                    'invoice_line_tax_ids' : [(6,False,[product.taxes_id.id])]
                    })],
                'number' : 'Contributo %s' % self.name,
                'date_invoice' : datetime.datetime.now()
            }
            refund = self.env['account.invoice'].create(attr)
            self.invoice_ids = [(4,refund.id,False)]
            refund.invoice_validate()
        else:
            self.invoice_ids.invoice_validate()

        self.state = 'closed'

    @api.one 
    def action_cancel(self):
        self.move_to_contribution.unlink()
        self.order_to_contribution.unlink()
        self.unlink()
    
    @api.one
    def _get_confirmed_qty(self):
    	qty = 0
        for line in self.order_to_contribution:
            qty += line.qty

        self.confirmed_qty = qty
        self.confirmed_value = self.confirmed_qty * self.value

    @api.constrains('value','qty')
    def control_value(self):
        message = ''
        if self.value == 0:
            message += 'Non credo che un valore zero sia cosa buona e giusta'
        if self.qty == 0 and self.contribution_type!='ads':
            message += 'Non credo che una quantità zero sia utile per calcolare il contributo'

        if message != '':
            raise exceptions.Warning(message)

    @api.one 
    def action_confirm(self):
        if self.state == 'confirmed':
            return True

        wh = self.env['stock.location'].search([('company_id','=',self.env.user.company_id.id),('active','=',True),
            ('usage','=','internal'),('scrap_location','=',False)])
        
        quants = self.env['stock.quant'].search([('location_id','=',wh.id),
            ('history_ids.picking_id.partner_id','=',self.partner_id.id),
            ('product_id','=',self.product_id.id),('reservation_id','=',False)])

        if self.contribution_type == 'revaluation':
            self._assign_revaluation(quants)
        elif self.contribution_type == 'valuexship':
            self._assign_valuexship()
            
        self.state = 'confirmed' 

        return True

    @api.multi
    def _assign_revaluation(self, quants):
        self.ensure_one()
        qta = self.qty
        ids = []
        invoice_ids = []
        for q in quants:
            if q.qty <= qta and qta > 0:
                move_ids = []
                for history in q.history_ids:
                    if len(history.picking_id.purchase_id) == 1:
                        attr = {
                            'move_ids' : [(4,history.id,False)],
                            'contribution_id' : self.id,
                            'qty' : q.qty,
                            'unit_value' : self.value
                        }
                        #creo nota di credito
                        for inv in history.picking_id.purchase_id.invoice_ids:
                            refund = inv.refund(datetime.datetime.now(),datetime.datetime.now(),'Rivalutazione %s' % inv.number)
                            refund.write({'origin':inv.number})
                            invoice_ids.append((4,refund.id,False))
                            for inv_line in refund.invoice_line_ids:
                                if inv_line.product_id.id != self.product_id.id:
                                    inv_line.unlink()
                                else:
                                    inv_line.write({'quantity':q.qty, 'price_unit' : self.value})

                        line_id=self.env['netaddiction.move.contribution'].create(attr)
                        ids.append((4,line_id.id,False))
                qta -= q.qty
            elif q.qty > qta and qta > 0:
                for history in q.history_ids:
                    if len(history.picking_id.purchase_id) == 1:
                        attr = {
                            'move_ids' : [(4,history.id,False)],
                            'contribution_id' : self.id,
                            'qty' : qta,
                            'unit_value' : self.value
                        }
                        #creo nota di credito
                        for inv in history.picking_id.purchase_id.invoice_ids:
                            refund = inv.refund(datetime.datetime.now(),datetime.datetime.now(),'Rivalutazione %s' % inv.number)
                            refund.write({'origin':inv.number})
                            invoice_ids.append((4,refund.id,False))
                            for inv_line in refund.invoice_line_ids:
                                if inv_line.product_id.id != self.product_id.id:
                                    inv_line.unlink()
                                else:
                                    inv_line.write({'quantity':qta, 'price_unit' : self.value})

                        line_id=self.env['netaddiction.move.contribution'].create(attr)
                        ids.append((4,line_id.id,False))
                qta = 0

        self.move_to_contribution = ids 
        self.invoice_ids = invoice_ids

    @api.multi 
    def _assign_valuexship(self):
        orders_line = self.env['sale.order.line'].search([('product_id','=',self.product_id.id),
            ('order_id.date_order','>=',self.date_start),('order_id.date_order','<=',self.date_finish)])
        qta = self.qty - self.confirmed_qty
        for line in orders_line:
            max_qta = 0
            #devo controllare che la quantità riservata sia del fornitore giusto
            for pick in line.order_id.picking_ids:
                #prendo le stockmove corrispondenti
                moves = self.env['stock.move'].search([('group_id','=',pick.group_id.id)])
                quants = self.env['stock.quant'].search([('reservation_id','=', moves.id),('history_ids.picking_id.partner_id','=',self.partner_id.id),
                    ('product_id','=',self.product_id.id)])
                for quant in quants:
                    max_qta += quant.qty
            #controllo le quantità, se la quantità già confermata è minore di quella massima allora continuo
            if qta > 0:
                if qta >= (line.product_qty - line.qty_reverse):
                    if (line.product_qty - line.qty_reverse) <= max_qta:
                        qty = (line.product_qty - line.qty_reverse)
                    else:
                        qty = max_qta
                else:
                    if qta <= max_qta:
                        qty = qta
                    else:
                        qty = max_qta
                
                attr = {
                    'order_id' : line.order_id.id,
                    'contribution_id' : self.id,
                    'qty' : qty,
                    'unit_value' : self.value
                }
                self.env['netaddiction.order.contribution'].create(attr)
                self.env.cr.commit()
                qta -= qty

    @api.onchange('partner_id')
    def _onchange_allowed_product(self):
        '''
        filtra la lista prodotti in base al forntire scelto
        i prodotti sono in magazzino o comunque sono valorizzati
        '''
        result = {}
        self.product_id = False
        self.qty = 0

        wh = self.env['stock.location'].search([('company_id','=',self.env.user.company_id.id),('active','=',True),
            ('usage','=','internal'),('scrap_location','=',False)])
        
        ids = []
        quants = self.env['stock.quant'].search([('location_id','=',wh.id),('history_ids.picking_id.partner_id','=',self.partner_id.id)])
        for q in quants:
            ids.append(q.product_id.id)

        result['domain'] = {'product_id': [
            ('id', 'in', ids),
            ]}
        return result

    @api.onchange('product_id')
    def _onchange_qty_product(self):
        """
        mette la quantità del prodotto che abbiamo in magazzino per quel fornitore
        """
        wh = self.env['stock.location'].search([('company_id','=',self.env.user.company_id.id),('active','=',True),
            ('usage','=','internal'),('scrap_location','=',False)])
        
        qty = 0
        quants = self.env['stock.quant'].search([('location_id','=',wh.id),('history_ids.picking_id.partner_id','=',self.partner_id.id),
            ('history_ids.product_id','=',self.product_id.id),('reservation_id','=',False)])
        for q in quants:
            qty+=q.qty

        self.qty = qty  


class QuantsToContribution(models.Model):
    _name="netaddiction.move.contribution"
    
    move_ids = fields.Many2many(string="Movimentazione",comodel_name="stock.move")
    contribution_id = fields.Many2one(string="Contributo", comodel_name="netaddiction.contribution", ondelete="cascade")
    qty = fields.Integer(string="Quantità")
    unit_value = fields.Float(string=
        "Valore unitario")

class OrdersToContribution(models.Model):
    _name = "netaddiction.order.contribution"
    
    order_id = fields.Many2one(string="Ordine",comodel_name="sale.order")
    contribution_id = fields.Many2one(string="Contributo", comodel_name="netaddiction.contribution", ondelete="set null")
    qty = fields.Integer(string="Quantità")
    unit_value = fields.Float(string=
        "Valore unitario")

class OrderContribution(models.Model):
    _inherit="sale.order"

    @api.one
    def action_cancel(self):
        res = super(OrderContribution,self).action_cancel()
        contribution = self.env['netaddiction.order.contribution'].search([('order_id','=',self.id)])
        if len(contribution) > 0:
            contribution.unlink()
        return res

class StockPickingContribution(models.Model):
    _inherit = 'stock.picking'

    @api.model 
    def create_reverse(self,attr,order_id):
        res = super(StockPickingContribution,self).create_reverse(attr,order_id)
        pids = {}
        #si prende i prodotti e le quantità di ogni rigo picking segnato come reso
        for line in attr['pack_operation_product_ids']:
            pids[int(line[2]['product_id'])] = line[2]['product_qty']
        
        contribution = self.env['netaddiction.order.contribution'].search([('order_id','=',int(order_id))])
        contribution.unlink()
        return res