# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class Gift(models.Model):
    _name = "netaddiction.gift"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Cliente", required=True)
    type_id = fields.Many2one(
        comodel_name='netaddiction.gift.type',
        string="Type", required = True)
    value = fields.Float(string="Valore")
    #reason = fields.Selection([('r','Rimborso'),('a','Altro')], string='Motivazione', default='r')

    @api.one
    @api.constrains('value')
    def _check_value(self):
        if self.value < 0.0:
            self.value = 0.0
            raise ValidationError("Il valore del gift deve essere maggiore uguale a zero")

    @api.one
    @api.constrains('partner_id')
    def _check_partner_id(self):

        if self.partner_id is None or self.partner_id.type != 'contact' :
            raise ValidationError("Il gift può essere assegnato solo a clienti")


    @api.one
    @api.constrains('partner_id', 'type_id')
    def _check_partner_id(self):
        to_search=[
            ('partner_id','=',self.partner_id.id),
            ('type_id','=',self.type_id.id)]        
        get = self.search(to_search)
        if len(get)>1:
            raise ValidationError("i seguenti tipi di gift esistono già per questo cliente")

   
class GiftCustomer(models.Model):
    _inherit = 'res.partner'
    gift_ids = fields.One2many(
        comodel_name='netaddiction.gift',
        inverse_name='partner_id',
        string='Gift')
    total_gift = fields.Float(compute='_compute_total_gift', string='Totale gift')
    got_gift = fields.Boolean(compute='_compute_got_gift', string='ha gift?')



    @api.depends('gift_ids')
    def _compute_total_gift(self):
        for record in self:
            for gift in record.gift_ids:
                record.total_gift += gift.value

    @api.depends('gift_ids')
    def _compute_got_gift(self):
        for record in self:
            record.got_gift = len(record.gift_ids) > 0

    @api.multi
    def new_customer_gift(self):

        view_id = self.env.ref('netaddiction_customer.netaddiction_sales_gift_form').id
        return {
            'name':'Nuova Gift',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'netaddiction.gift',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'context':{
                'default_partner_id' : self.id,
                 },
        }


    @api.one
    def add_gift_value(self,to_add, gift_type):
        """
        gift_type = stringa reason del gift type
        """
        found = False
        if self.got_gift:
            for gift in self.gift_ids:
                if gift.type_id.reason == gift_type:
                    #print "gift value %s to add %s" %(gift.value, to_add)
                    gift.value += to_add
                    #print "gift value %s to add %s" %(gift.value, to_add)
                    found = True

                    break
        if not found:
            gtype = self.env["netaddiction.gift.type"].search([("reason","=",gift_type)])
            if gtype:
                self.env["netaddiction.gift"].create({'partner_id': self.id,'value':to_add, 'type_id':gtype.id})

    @api.one
    def remove_gift_value(self,to_rmv):
        if self.got_gift:
            remaining = to_rmv
            gifts = [gift for gift in self.gift_ids]
            gifts.sort(key=lambda gift: gift.type_id.priority)
            for gift in gifts:
                if gift.value > remaining:
                    gift.value -= remaining
                    remaining = 0.0
                    break
                else:
                    remaining -= gift.value
                    gift.unlink()




class GiftType(models.Model):
    _name = "netaddiction.gift.type"
    _rec_name = 'reason'
    _sql_constraints = [
    ('reason_unique', 'unique(reason)', 'Questo tipo di gift esiste già!')]
    reason = fields.Char('Motivazione',required=True, unique=True)
    priority = fields.Selection([(1,'Molto Alta'),(2,'Alta'),(3,'Media'),(4,'Bassa'),(5,'Molto Bassa')], string='Priorità', default=2,required=True)
    gift_ids = fields.One2many(
        comodel_name='netaddiction.gift',
        inverse_name='type_id',
        string='Gift')

