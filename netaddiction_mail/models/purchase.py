# -*- coding: utf-8 -*-

from openerp import api, models
from openerp.exceptions import ValidationError
import datetime
import StringIO
import base64
import sys

class Purhcase(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_cancel(self):
        for order in self:
            for line in order.order_line:
                line.send_mail_cancel(0,True)

        return super(Purhcase,self).button_cancel()

    @api.one
    def action_rfq_send(self):
        users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_purchase_user_plus")
        to_partner = self.env['res.partner'].search([('parent_id','=',self.partner_id.id),('send_contact_purchase_orders','=',True)])
        recipients = []
        for res in to_partner:
            recipients.append(res)
        for u in users:
            recipients.append(u)

        if len(recipients) == 0:
            raise ValidationError("Nessun contatto di questo fornitore può ricevere gli ordini.")

        email_from = 'acquisti@multiplayer.com'
        reply_to = 'riccardo.ioni@netaddiction.it'

        subject = 'Ordine Articoli da Multiplayer.com n. ordine %s (%s)' % (self.id,self.partner_id.name)

        
        body = """
        Ordine Articoli da Multiplayer.com n. ordine %s del %s <br><br>

        =================================================<br>
        %s 
        =================================================<br><br>

        Totale Ordine: EUR %s <br><br>

        Vi preghiamo di evadere quanto prima possibile tutti i prodotti disponibili e di mantenere in backorder eventuali prodotti in prenotazione o non disponibili.<br>
        Chiediamo inoltre di volerci avvisare se in ordine dovessero esserci prodotti fuori catalogo o non reperibili.<br>
        Questo ordine NON sostituisce i precedenti.<br>
        Per qualsiasi evenienza potrete contattare la nostra logistica al numero 07442462131.<br><br>

        Cordialmente,<br>
        Multiplayer.com
        """ 
        rows = ''
        for line in self.order_line:
            code = False
            for i in line.product_id.seller_ids:
                if i.name == self.partner_id:
                    code = i.product_code

            text = '%s x %s - EUR %s - %s <br>' % (int(line.product_qty),code,line.price_unit,line.product_id.display_name)
            rows += text

        variables = (self.id,datetime.date.today(),rows,self.amount_untaxed)

        body = body % variables

        attach = False
        if self.partner_id.name.lower() == 'terminalvideo':
            file = ""

            for line in self.order_line:
                text = '%s;%s;%s\r\n' % (line.product_id.barcode,int(line.product_qty),line.price_unit)
                file += text

            file1 = StringIO.StringIO()
            file1.write(file)

            data_attach = {
                    'name': 'ord_tvideo.txt',
                    'datas': base64.b64encode(file1.getvalue()),
                    'datas_fname': 'ord_tvideo.txt',
                    'description': 'ord_tvideo.txt',
            }

            attach = self.env['ir.attachment'].create(data_attach)

        if attach:
            ids = [attach.id]
            self.env["netaddiction.email.dispatcher"].send_mail(body, subject, email_from, recipients, ids, reply_to)
        else:
            self.env["netaddiction.email.dispatcher"].send_mail(body, subject, email_from, recipients, None,reply_to)
        
        if self.state == 'draft':
            self.state = 'sent'

class PurchaseOrdersLine(models.Model):
    _inherit="purchase.order.line"


    @api.one 
    def send_mail_cancel(self,qty, unlink = False):
    	subject = "Importante cancellazione ordine prodotto - Multiplayer.com - n. ordine %s" % (self.id,)
        email_from = 'acquisti@multiplayer.com'
        reply_to = 'riccardo.ioni@netaddiction.it'
        recipients = []
        to_partner = self.env['res.partner'].search([('parent_id','=',self.order_id.partner_id.id),('send_contact_purchase_orders','=',True)])
        for res in to_partner:
            recipients.append(res)
        users = self.env["netaddiction.email.dispatcher"].get_users_from_group("netaddiction_acl.netaddiction_purchase_user_plus")
        for u in users:
            recipients.append(u)
        if len(recipients) == 0:
            raise ValidationError("Nessun contatto di questo fornitore può ricevere gli ordini.")
        code = False
        for i in self.product_id.seller_ids:
            if i.name == self.partner_id:
                code = i.product_code
        qta = 0
        query = self.search([('product_id','=',self.product_id.id),('state','=','purchase'),('order_id.partner_id','=',self.order_id.partner_id.id)])
        for q in query:
            qta += q.product_qty
        line = "%s | COD.FOR. %s | EAN %s" % (self.product_id.display_name,code,self.product_id.barcode)
        
        qty_to_down = self.product_qty - qty
        body = """
        Gentile Fornitore, <br>
        desidero informarti che abbiamo cancellato l'ordine del seguente prodotto:<br><br>
        =================================================<br>
        %s 
        =================================================<br><br>
        DATA ORDINE: %s<br>
        PREZZO: %s<br>
        QTA: %s<br>
        NUOVA QUANTITA' IN BACKORDER: %s<br><br>
        Pertanto ti chiediamo di rimuoverlo dal vostro backorder.<br>
        Qualora il prodotto venisse spedito nonostante la nostra cancellazione verra' immediatamente reso e la fattura relativa bloccata.<br>
        Distinti saluti,<br>
        Multiplayer.com
        """ % (line,self.order_id.date_order,self.price_unit,int(qty_to_down),int(qta-qty_to_down))
        
        self.env["netaddiction.email.dispatcher"].send_mail(body, subject, email_from, recipients, None,reply_to)
        
        if not unlink:
            self.update_picks(qty_to_down)


    @api.one 
    def update_picks(self,qty_to_down):
        for pick in self.order_id.picking_ids:
            if pick.state != 'done':
                for popi in pick.pack_operation_product_ids:
                    if popi.product_id.id == self.product_id.id:
                        popi.product_qty = popi.product_qty - qty_to_down 
                        if popi.product_qty == 0:
                            popi.unlink()


    @api.one
    def write(self,values):
        if 'product_qty' in values.keys():
            if self.product_qty < values['product_qty']:
                raise Warning('Per Aggiungere quantità devi fare un nuovo Ordini a questo fornitore di questo prodotto.')
            else:
                if self.order_id.state == 'purchase':
                    self.send_mail_cancel(values['product_qty'])


        return super(PurchaseOrdersLine,self).write(values)





