from openerp import models, fields, api
from openerp.addons.celery_queue.decorators import CeleryTask

class AccountPayment(models.Model):
    """docstring for AccountPayment"""
    _inherit = 'account.payment'

    order_id = fields.Many2one(comodel_name='sale.order', string='Ordine')

    #replica dei dati della cc 
    cc_token = fields.Char(string='Token')
    cc_last_four = fields.Char(string='Indizio')
    cc_month = fields.Integer(string='Mese')
    cc_year =  fields.Integer(string='Anno')
    cc_name = fields.Char(string='Titolare')
    cc_status = fields.Selection([('init','Da autorizzare'),('auth','Autorizzato'),('commit','Pagato')])
    cc_type = fields.Char(string='Tipo Carta')
    cc_trans_id = fields.Char(string='Trans_id')

    cc_selection = fields.Many2one( "netaddiction.partner.ccdata", string="associare carta")

    paypal_transaction_id = fields.Char(string='ID transazione paypal')
    sofort_transaction_id = fields.Char(string='ID transazione sofort')

    @CeleryTask(queue='sequential')
    @api.multi
    def delay_post(self):
        return super(AccountPayment, self).post()

    @api.onchange('cc_selection')
    def onchange_cc_selection(self):
        self.cc_token = self.cc_selection.token
        self.cc_last_four = self.cc_selection.last_four
        self.cc_month = self.cc_selection.month
        self.cc_year = self.cc_selection.year
        self.cc_name = self.cc_selection.name
        self.cc_type = self.cc_selection.ctype
        self.cc_status = 'init'
        self.cc_selection = None

class OrderPayment(models.Model):
    """docstring for OrderPayment"""
    _inherit = 'sale.order'

    #collegamento all'ordine
    account_payment_ids = fields.One2many('account.payment','order_id', string='Pagamenti')


