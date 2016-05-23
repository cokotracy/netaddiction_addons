# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp import exceptions
import datetime
from pprint import pprint

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
                                                       ('confirmed','Confermato')
                                                      ],default="draft")

    move_to_contribution = fields.Many2many(string="Righe Contributi/Movimentazioni", comodel_name="netaddiction.move.contribution")
    order_to_contribution = fields.One2many(string="Righe Ordini/Movimentazioni", comodel_name="netaddiction.order.contribution", inverse_name="contribution_id")

    #controlli per valuexship
    confirmed_qty = fields.Integer(string="Quantità Contribuita", compute="_get_confirmed_qty")
    confirmed_value = fields.Float(string="Valore Contribuito", compute="_get_confirmed_qty")

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
                        line_id=self.env['netaddiction.move.contribution'].create(attr)
                        ids.append((4,line_id.id,False))
                qta = 0

        self.move_to_contribution = ids 

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
                if qta >= line.product_qty:
                    if line.product_qty <= max_qta:
                        qty = line.product_qty
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