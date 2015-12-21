# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID
import base64
from HTMLParser import HTMLParser
import email
import re
from datetime import datetime,date

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
            ],string="Tipo",default="phone")
    unread_messages = fields.Integer('Messaggi non letti')

    state = fields.Selection([
        ('draft', "Nuovo"),
        ('working', "In Elaborazione"),
        ('reopen', "Riaperto"),
        ('close', "Chiuso"),
    ])

    satisfaction_rate = fields.Selection([
        ('none' , 'Nessuno'),
        ('negative' , 'Negativo'),
        ('neutral' , 'Normale'),
        ('positive' , 'Positivo')
        ],default="none")

    @api.model
    def create(self,values):
        res = super(Issue,self).create(values)

        if 'close_immediately' in values.keys():
            if values['close_immediately']:
                res.action_close()

        return res

    @api.one
    def write(self,values):
        logger = False
        message = u"""
        Supporto Clienti Modificato:<br>
        <ul>
        """

        if 'order_id' in values.keys():
            logger=True
            new_order = False
            if values['order_id'] is not False:
                result = self.env['sale.order'].search([('id','=',int(values['order_id']))])
                if len(result)>0:
                    new_order = result.name
            message = message + u"<li>Ordine : " + str(self.order_id.name) + u" -> " +str(new_order) + u"</li>"
        if 'company_id' in values.keys():
            logger=True
            new_company = False
            if values['company_id'] is not False:
                result = self.env['res.company'].search([('id','=',int(values['company_id']))])
                if len(result)>0:
                    new_company = result.name
            message = message + u"<li>Azienda : " + str(self.company_id.name) + u" -> " +str(new_company) + u"</li>"
        if 'issue_type_src' in values.keys():
            logger=True
            message = message + u"<li>Tipo : " + str(self.issue_type_src) + u" -> " +str(values['issue_type_src']) + u"</li>"
        if 'user_id' in values.keys():
            logger=True
            new_user = False
            if values['user_id'] is not False:
                result = self.env['res.users'].search([('id','=',int(values['user_id']))])
                if len(result)>0:
                    new_user = result.name
            message = message + u"<li>Assegnato a : " + str(self.user_id.name) + u" -> " +str(new_user) + u"</li>"
        if 'priority' in values.keys():
            logger=True
            message = message + u"<li>Priorità : " + str(self.priority) + u" -> " +str(values['priority']) + u"</li>"
        if 'partner_id' in values.keys():
            new_user = False
            if values['partner_id'] is not False:
                result = self.env['res.partner'].search([('id','=',int(values['partner_id']))])
                if len(result)>0:
                    new_user = result.name
            logger=True
            message = message + u"<li>Contatto : " + str(self.partner_id.name) + u" -> " +str(new_user) + u"</li>"
        if 'email_from' in values.keys():
            logger=True
            message = message + u"<li>E-mail : " + str(self.email_from) + u" -> " +str(values['email_from']) + u"</li>"
        #if 'description' in values.keys():
        #    logger=True
        #    message = message + u"<li>Descrizione : " + str(self.description) + u" -> " +str(values['description']) + u"</li>"
        if 'tag_ids' in values.keys():
            logger=True
            message = message + u"<li>Tags : " + str(self.tag_ids) + u" -> " +str(values['tag_ids']) + u"</li>"

        message = message + u"</ul>"

        if logger:
            self._put_log(message)

        return super(Issue,self).write(values)

    @api.one
    def action_draft(self):
        self.state = 'draft'
        message = {
            'body' : self._get_message_new()
        } 
        self._post_mail(message,comment_else=False)

        message = u"""
        Supporto Clienti Aperto:<br>
        <ul>
            <li>Stato : %s</li>
            <li>Tipo : %s</li>
            <li>Azienda : %s</li>
            <li>Priorità : %s</li>
            <li>Assegnato a : %s</li>
            <li>Ordine : %s</li>
            <li>Contatto : %s</li>
            <li>E-mail : %s</li>
        </ul>
        """ % (self.state,self.issue_type_src,self.company_id.name,self.priority,self.user_id.name,self.order_id.name,
                self.partner_id.name,self.email_from)
        self._put_log(message)

    @api.multi
    def action_working(self):
        self.state = 'working'
        self.user_id = self.env.user.id
        self.unread_messages = 0

        message = u"""
        Cambio Stato:<br>
        <ul>
            <li>Stato: draft -> working</li>
        </ul>
        """
        self._put_log(message)


    @api.multi
    def action_close(self):
        self.state = 'close'
        self.unread_messages = 0

        #Setto la data di chiusura
        self.date_closed = datetime.now()

        message = {
            'body' : self._get_message_close()
        } 
        self._post_mail(message,comment_else=False)

        message = u"""
        Cambio Stato:<br>
        <ul>
            <li>Stato: working -> close</li>
        </ul>
        """
        self._put_log(message)

    @api.one
    def action_reopen(self):
        self.write({'state':'reopen'})
        message = u"""
        Cambio Stato:<br>
        <ul>
            <li>Stato: close -> reopen</li>
        </ul>
        """
        self._put_log(message)

    @api.one
    def action_reclose(self):
        self.write({'state':'close','unread_messages':0})
        
        message = {
            'body' : self._get_message_close()
        } 
        self._post_mail(message,comment_else=False)

        message = u"""
        Cambio Stato:<br>
        <ul>
            <li>Stato: reopen -> close</li>
        </ul>
        """
        self._put_log(message)

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


    @api.one
    @api.constrains('user_id')
    def _send_mail_to_user(self):
        base_url = self.env['ir.config_parameter'].search([('key','=','web.base.url')])
        url = u"%s/web#id=%d&view_type=form&model=project.issue" % (base_url.value,self.id)
        message = u"Ti è stato assegnato un supporto cliente al seguente link %s" % (url,) 

        template = self._get_template_email()
        if len(template)>0 and self.user_id.id != self.env.user.id and 'fetchmail_cron_running' not in self.env.context:
            mail = template.with_context(message=message).generate_email(self.id)
            mail['email_from'] = self._get_email_from()
            mail['reply_to'] = self._get_email_from()
            mail['email_to'] = self.user_id.email
        
            email = self.env['mail.mail'].create(mail)
            email.send()
        

    @api.onchange('email_from')
    def _change_email(self):
        if self.email_from is not False:
            result = self.env['res.partner'].search([('email','=',self.email_from)])
            if len(result)==1:
                self.partner_id = result.id

    @api.onchange('order_id')
    def _change_order(self):
        if len(self.order_id)==1:
            self.partner_id = self.order_id.partner_id.id

    @api.onchange('partner_id')
    def _change_partner(self):
        self.email_from = self.partner_id.email

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
    def _get_settings(self):
        to_search=[('company_id','=',self.company_id.id)]
        res = self.env['netaddiction.project.issue.settings.companymail'].search(to_search)
        return res

    def _get_email_from(self):
        res = self._get_settings()
        return res.email

    def _get_template_email(self):
        res = self._get_settings()
        return res.template_id

    def _get_message_new(self):
        res = self._get_settings()
        return res.message_new

    def _get_message_close(self):
        res = self._get_settings()
        return res.message_close

    def _post_comment(self,args):
        attr = {
                'subtype_id' : args['subtype_id'], 
                'res_id' : self.id,
                'body' : args['body'],
                'model' : 'project.issue',
                'author_id' : self.env.user.partner_id.id,
                'message_type' : 'comment',
            }

        res = self.env['mail.message'].create(attr)
        return res

    def _post_mail(self,args,comment_else = True):
        template = self._get_template_email()
        if len(template)>0:
            mail = template.with_context(message=args['body']).generate_email(self.id)
            mail['email_from'] = self._get_email_from()
            mail['reply_to'] = self._get_email_from()
            mail['email_to'] = self.email_from

            if 'attachment_ids' in args.keys():
                mail['attachment_ids'] = [(6,0,args['attachment_ids']),]
        
            email = self.env['mail.mail'].create(mail)
            email.send()
        
        if comment_else:
            return self._post_mail_comment(args)
        else:
            return email
        

    def _post_mail_comment(self,args):
        attr = {
            'subtype_id' : 1, 
            'res_id' : self.id,
            'body' : args['body'],
            'model' : 'project.issue',
            'author_id' : self.env.user.partner_id.id,
            'message_type' : 'comment',
        }
        if 'attachment_ids' in args.keys():
            attr['attachment_ids'] = [(6,0,args['attachment_ids']),]

        return self.env['mail.message'].create(attr)

    def _post_comment_from_mail(self,args):
        m2m_attachment_ids = []
        body = self._replace_src(args['body'])

        attr = {
            'subtype_id' : 1, 
            'res_id' : self.id,
            'body' : body,
            'model' : 'project.issue',
            'author_id' : args['author_id'],
            'message_type' : 'comment',
        }

        for name, content in args['attachments']:
            if name == 'original_email.eml':
                body = self._replace_src(content)

            if isinstance(content, unicode):
                content = content.encode('utf-8')
            data_attach = {
                    'name': name,
                    'datas': base64.b64encode(str(content)),
                    'datas_fname': name,
                    'description': name,
                    'res_model': 'project.issue',
                    'res_id': self.id,
            }
            m2m_attachment_ids.append((0, 0, data_attach))
        attr['attachment_ids']=m2m_attachment_ids

        return self.env['mail.message'].create(attr)

    #############
    #REPLACE IMG#
    #############

    def _replace_src(self,body):
        #installare beautifulsoap
        td = TagDropper(['img'])
        td.feed(body)
        body = td.get_text()
        return body

    #############################
    #GESTIONE LOG MESSAGE E MAIL#        
    #############################
    @api.one
    def _put_log(self,message):

            
        attr = {
            'subtype_id' : 2, 
            'res_id' : self.id,
            'body' : message,
            'model' : 'project.issue',
            'message_type' : 'comment',
        }
        self.env['mail.message'].create(attr)
    
    @api.one
    def _message_post_new(self,args,ct):

        """
        nuovo message post per questa classe con le api v8
        """
        #per prima cosa aggiorno la data di ultima modifica
        self.write({'date_action_last':fields.datetime.now()})

        if 'message_type' in args.keys():
            if args['message_type'] == 'comment' and args['subtype_id']==2:
                #qui è una nota interna
                res = self._post_comment(args)
                self._zero_unread_message()

            if 'fetchmail_cron_running' in ct.keys() and 'subtype_id' not in args.keys():
                #email ricevuta
                attr = {
                    'issue_type_src' : 'email',
                }
                
                to = args['to']
                res = self.env['netaddiction.project.issue.settings.companymail'].search([('email','ilike',to)])
               
                if len(res)==1:
                    attr['company_id'] = res.company_id.id
                    
                self.write(attr)

                res = self._post_comment_from_mail(args)

                self._add_unread_message()

                if self.state == 'close':
                    self.action_reopen()
            else:

                if args['subtype_id'] is False:
                    #qui è una email
                    res = self._post_mail(args)
                    self._zero_unread_message()

            return res.id

        return None


    def _add_unread_message(self):
        attr = {
            'unread_messages' : self.unread_messages + 1
        }
        self.write(attr)

    def _zero_unread_message(self):
        attr = {
            'unread_messages' : 0
        }
        self.write(attr)

    @api.cr_uid_ids_context
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, cr, uid, thread_id, subtype=None, context=None, **kwargs):
        return self._message_post_new(cr,uid,thread_id,kwargs,context)


class OrderIssue(models.Model):
    _inherit = 'sale.order'

    issue_id = fields.One2many('project.issue','order_id')

    number_of_issue = fields.Integer(string="Problematiche",compute="_count_issue")

    @api.one
    def _count_issue(self):
        res = self.env['project.issue'].search([('order_id','=',self.id)])
        self.number_of_issue = len(res)

    @api.multi
    def new_issue(self):
        view_id = self.env.ref('netaddiction_customer_care.netaddiction_cc_project_issue_form_view').id
        
        return {
            'name':'Nuova Problematica',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'project.issue',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'context':{'default_order_id':self.id,
                'default_issue_type_src':'manual',
                'default_company_id':self.company_id.id},
        }


class TagDropper(HTMLParser):
    def __init__(self, tags_to_drop, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self._text = []
        self._tags_to_drop = set(tags_to_drop)
    def clear_text(self):
        self._text = []
    def get_text(self):
        return ''.join(self._text)
    def handle_starttag(self, tag, attrs):
        if tag not in self._tags_to_drop:
            self._text.append(self.get_starttag_text())
    def handle_endtag(self, tag):
        self._text.append('</{0}>'.format(tag))
    def handle_data(self, data):
        self._text.append(data)