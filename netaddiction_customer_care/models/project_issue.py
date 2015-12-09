# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

EMAIL_FROM = 'noreply@netaddiction.it'

class Issue(models.Model):
    _inherit = 'project.issue'

    order_id = fields.Many2one('sale.order',ondelete="restrict",
        string="Ordine")

    state = fields.Selection([
        ('draft', "Nuovo"),
        ('working', "In Elaborazione"),
        ('close', "Chiuso"),
    ])

    @api.one
    def action_draft(self):
        self.state = 'draft'

        #caso in cui la mail arriva dall'esterno
        message = """Gentile Cliente,<br>
                Abbiamo preso in carico la sua richiesta di assistenza,verrà ricontattato a breve da un nostro operatore."""
        if self.description is not False:
            message += """<br>Descrizione problema:<br>""" + str(self.description.decode('utf-8'))

        self._send_mail(message)

    @api.multi
    def action_working(self):
        self.state = 'working'
        self.user_id = self.env.user.id

    @api.multi
    def action_close(self):
        self.state = 'close'

        message = """Gentile Cliente,<br>
        La sua richiesta di assistenza è stata chiusa.<br>
        La preghiamo di compilare il questionario seguente."""

        self._send_mail(message)

    @api.one
    @api.constrains('order_id', 'partner_id','email_from')
    def _check_one_of(self):
        if self.email_from is False and len(self.order_id)==0 and len(self.partner_id)==0 :
            raise ValidationError("Devi inserire almeno uno tra ordine,contatto,email")

        if len(self.order_id)>0:
            if self.order_id.partner_id.id != self.partner_id.id:
                raise ValidationError("Il contatto inserito non corrisponde al cliente dell'ordine inserito")

            if self.order_id.partner_id.email != self.email_from:
                raise ValidationError("L'e-mail inserita non corrisponde alla e-mail dell'ordine inserito")

    @api.onchange('email_from')
    def _change_email(self):
        if self.email_from is not False:
            self.partner_id = False
            result = self.env['res.partner'].search([('email','=',self.email_from)])
            if len(result)==1:
                self.partner_id = result.id

    @api.onchange('order_id')
    def _change_order(self):
        if len(self.order_id)==1:
            prev = self.order_id 
            self.partner_id = False
            self.email_from = False
            self.partner_id = self.order_id.partner_id.id

    @api.one
    def set_desc_from_msg(self):
        for msg in self.message_ids:
            if msg.message_type == 'email':
                self.description=msg.body
    #####################
    #    SEND e-mail    #
    #####################
    def _send_mail(self,message):
        
        if len(self.partner_id)==0:
            attr = {
                'subject' : self.name,
                'email_from' : EMAIL_FROM,
                'email_to' : self.email_from,
                'message_type' : 'email',
                'body_html' : message ,
                'auto_delete' : 1,
                'reply_to' : EMAIL_FROM,
            }
            email = self.env['mail.mail'].create(attr)
            email.send()

        else:
            attr = {
                    'subtype_id' : 1, #discussione
                    'res_id' : self.id,
                    'subject' : self.name,
                    'body' : message,
                    'model' : 'project.issue',
                    'author_id' : self.env.user.partner_id.id,
                    'message_type' : 'comment',
                    'partner_ids' : [(4,self.partner_id.id)]
                    }

            message_id = self.env['mail.message'].create(attr)
            message_id.unlink()

class OrderIssue(models.Model):
    _inherit = 'sale.order'

    issue_id = fields.One2many('project.issue','order_id')
