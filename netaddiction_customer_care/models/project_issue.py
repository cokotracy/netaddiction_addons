# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID

class Issue(models.Model):
    _inherit = 'project.issue'

    order_id = fields.Many2one('sale.order',ondelete="restrict",
        string="Ordine")
    close_immediately = fields.Boolean('Chiudi immediatamente',help="se True allora crea un ticket già chiuso",default=False)
    issue_type_src = fields.Selection([
                ('phone','Telefonico'),
                ('manual','Manuale'),
                ('email','E-mail'),
                ('ebay','Ebay'),
                ('fb','Facebook'),
            ],string="Tipo")
    unread_messages = fields.Integer('Messaggi non letti')

    state = fields.Selection([
        ('draft', "Nuovo"),
        ('working', "In Elaborazione"),
        ('close', "Chiuso"),
    ])


    @api.model
    def create(self,values):
        res = super(Issue,self).create(values)

        if 'close_immediately' in values.keys():
            if values['close_immediately']:
                res.action_close()

        return res

    @api.one
    def action_draft(self):
        self.state = 'draft'

        #caso in cui la mail arriva dall'esterno
        message = u"""Gentile Cliente,<br>
                Abbiamo preso in carico la sua richiesta di assistenza,verrà ricontattato a breve da un nostro operatore."""
        if self.description is not False:
            message += u"""<br>Descrizione problema:<br> %s""" % self.description

        self._send_mail(message)

    @api.multi
    def action_working(self):
        self.state = 'working'
        self.user_id = self.env.user.id
        self.unread_messages = 0

    @api.multi
    def action_close(self):
        self.state = 'close'
        self.unread_messages = 0

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
        if self.description is False:
            for msg in self.message_ids:
                if msg.message_type == 'comment':
                    self.description=msg.body
                    break

    #####################
    #    SEND e-mail    #
    #####################
    def _send_mail(self,message):
        
        attr = {
            'subject' : u"Ticket #%d: %s" % (self.id,self.name),
            'email_from' : self._get_email_from(),
            'email_to' : self.email_from,
            'message_type' : 'email',
            'body_html' : message ,
            'auto_delete' : 1,
            'reply_to' : self._get_email_from(),
            'res_id' : self.id,
            'model' : 'project.issue',
        }
        email = self.env['mail.mail'].create(attr)
        email.send()

        attr = {
            'subtype_id' : 1, 
            'res_id' : self.id,
            'subject' : self.name,
            'body' : message,
            'model' : 'project.issue',
            'author_id' : self.env.user.partner_id.id,
            'message_type' : 'comment',
        }

        return self.env['mail.message'].create(attr)

    def _send_mail_old(self,cr,uid,thread_id,context,kwargs):
        if type(thread_id) is list:
            thread_id = thread_id[0]

        pi_id = self.pool['project.issue'].search(cr, uid, [('id', '=', thread_id)])
        obj = self.pool['project.issue'].read(cr, uid, pi_id)

        attr = {
            'subject' : u"Ticket #%d: %s" % (thread_id,obj[0]['name']),
            'email_from' : self._get_email_from_old(cr,uid,thread_id),
            'email_to' : obj[0]['email_from'],
            'message_type' : 'email',
            'body_html' : kwargs['body'] ,
            'auto_delete' : 1,
            'reply_to' : self._get_email_from_old(cr,uid,thread_id),
            'model' : 'project.issue',
            'res_id' : thread_id,
            }

        if 'attachment_ids' in kwargs.keys():
            attr['attachment_ids'] = [(6,0,kwargs['attachment_ids']),]

        ids_m = self.pool.get('mail.mail').create(cr,uid,attr)
        res = self.pool.get('mail.mail').send(cr, uid, [ids_m], context=context)   

        return res    

    def _post_comment_from_mail(self,cr,uid,thread_id,kwargs):

        if type(thread_id) is list:
            thread_id = thread_id[0]

        pi_id = self.pool['project.issue'].search(cr, uid, [('id', '=', thread_id)])
        obj = self.pool['project.issue'].read(cr, uid, pi_id)

        attr = {
            'subtype_id' : 1, 
            'res_id' : thread_id,
            'subject' : obj[0]['name'],
            'body' : kwargs['body'],
            'model' : 'project.issue',
            'message_type' : 'comment',
            }

        # TODO: PROCESSARE GLI ALLEGATI IN ARRIVO, kwargs['attachments']

        if 'attachment_ids' in kwargs.keys():
            attr['attachment_ids'] = [(6,0,kwargs['attachment_ids']),]

        res = self.pool['mail.message'].create(cr,uid,attr)

        return res
        


    def _get_email_from(self):
        to_search=[('company_id','=',self.company_id.id)]
        res = self.env['netaddiction.project.issue.settings.companymail'].search(to_search)
        return res.email

    def _get_email_from_old(self,cr,uid,thread_id):
        
        pi_id = self.pool['project.issue'].search(cr, uid, [('id', '=', thread_id)])
        obj = self.pool['project.issue'].read(cr, uid, pi_id)
        res = self.pool['netaddiction.project.issue.settings.companymail'].search_read(cr, uid, [('company_id','=',obj[0]['company_id'][0])])
        return res[0]['email']
    #############################
    #GESTIONE LOG MESSAGE E MAIL#        
    #############################

    @api.cr_uid_ids_context
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, cr, uid, thread_id, subtype=None, context=None, **kwargs):
        """
        Fa l'override del metodo che gestisce il thread di messaggi nella issue.
        Sostitusco alcuni parametri per semplificare lo scambio di mail
        """

        if context is None:
            context = {}

        if subtype == 'mail.mt_comment':
            if type(thread_id) is list:
                thread_id = thread_id[0]

            pi_id = self.pool['project.issue'].search(cr, uid, [('id', '=', thread_id)])
            obj = self.pool['project.issue'].read(cr, uid, pi_id)
            
            #qui se è un messaggio scritto dal backoffice
            res = None
            if 'subtype_id' in kwargs.keys():
                
                if kwargs['subtype_id']==2 and kwargs['message_type']=='comment':
                    #è una nota interna mi comporto di default
                    res = super(Issue, self).message_post(cr, uid, thread_id, subtype=subtype, context=context, **kwargs)
                    self.write(cr, SUPERUSER_ID, thread_id, {'unread_messages': 0}, context=context)

                if kwargs['subtype_id'] is False and 'fetchmail_cron_running' not in context.keys():
                    #è uan e-mail sendo e posto un commento
                    mail_id = self._send_mail_old(cr,uid,thread_id,context,kwargs)
                    res = self._post_comment_from_mail(cr,uid,thread_id,kwargs)
                    self.write(cr, SUPERUSER_ID, thread_id, {'unread_messages': 0}, context=context)
                    
                return res

            if 'fetchmail_cron_running' in context.keys():
                #email ricevuta dall'esterno
                
                #aggiorno il contatore dei messaggi non letti
                self.write(cr, SUPERUSER_ID, thread_id, {'unread_messages': int(obj[0]['unread_messages'])+1,'issue_type_src':'email'}, context=context)

                res = self._post_comment_from_mail(cr,uid,thread_id,kwargs)
                #res = super(Issue, self).message_post(cr, uid, thread_id, subtype=subtype, context=context, **kwargs)
                #self.pool['mail.message'].write(cr, SUPERUSER_ID, res, {'message_type': 'comment'}, context=context)

                return res
        if thread_id and subtype:
            self.write(cr, SUPERUSER_ID, thread_id, {'date_action_last': fields.datetime.now()}, context=context)
        return None
    

class OrderIssue(models.Model):
    _inherit = 'sale.order'

    issue_id = fields.One2many('project.issue','order_id')
