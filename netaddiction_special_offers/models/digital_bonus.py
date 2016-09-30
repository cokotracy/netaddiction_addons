# -*- coding: utf-8 -*-
import csv
import base64
import io
from openerp import models, fields, api
from openerp.exceptions import Warning



class DigitalBonus(models.Model):

    _name = "netaddiction.specialoffer.digital_bonus"

    csv_file = fields.Binary('File')

    active = fields.Boolean(string='Attivo', help="Permette di spengere l'offerta senza cancellarla", default=True)
    name = fields.Char(string='Titolo', required=True)
    products_ids = fields.Many2many('product.product', 'prod_codes_rel', 'code_id', 'prod_id', 'Prodotti')
    code_ids = fields.One2many('netaddiction.specialoffer.digital_code', 'bonus_id', string='Codici associati')
    text = fields.Text("testo offerta")
    mail_text = fields.Text("testo mail")
    image = fields.Binary("Immagine", attachment=True,
        help="Limitata a 1024x1024px.")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True)
    qty_limit = fields.Integer(string="Quantità limite", default=0, help="zero è illimitato")
    qty_sold = fields.Integer(string="Quantità venduta", default=0)
    assign_codes = fields.Boolean(string='Assegna Codici', help="assegna o prenota i codici agli ordini, se disattivato verrà solamente ", default=True)

    @api.one
    @api.constrains('qty_limit', 'qty_sold')
    def _check_limit(self):
        if self.assign_codes and self.qty_limit > 0 and self.qty_sold >= self.qty_limit:
            self.active = False

    @api.one
    def process_file(self):
        if self.assign_codes and self.csv_file:
            decoded64 = base64.b64decode(self.csv_file)
            decodedIO = io.BytesIO(decoded64)
            reader = csv.reader(decodedIO)

            for line in reader:
                if not self.env["netaddiction.specialoffer.digital_code"].search([("bonus_id", "=", self.id), ("code", "=", line[0])]):
                    self.env["netaddiction.specialoffer.digital_code"].create({
                        'code': line[0],
                        'order_id': None,
                        'bonus_id': self.id,
                        'sent': False,
                        'date_sent': None,
                        'sent_by': None
                    })

            self.csv_file = None

        else:
            raise Warning("nessun file selezionato")

    @api.one
    def assign_old(self):
        if not self.active or not self.assign_codes:
            return
        id_list = [prod.id for prod in self.products_ids]
        orders = self.env["sale.order"].search([("order_line.product_id", "in", id_list), ("state", "in", ("sale", "problem", "partial_done", "done"))], order="date_order")
        if not orders:
            return
        codes = [code for code in self.code_ids if not code.sent and not code.order_id]
        if not codes:
            return
        for order in orders:
            codes_in_order = [code for code in order.code_ids if code.bonus_id.id == self.id]
            if codes_in_order:
                continue
            order_lines = [ol for ol in order.order_line if ol.product_id.id in id_list]
            for ol in order_lines:
                counter = 0
                while counter < ol.product_uom_qty and codes:
                    code = codes.pop(0)
                    code.order_id = order.id
                    code.order_line_id = ol.id
                    counter += 1
                    self.qty_sold += 1

    @api.one
    def send_all_valid(self):
        codes = self.env["netaddiction.specialoffer.digital_code"].search([("bonus_id", "=", self.id), ("order_id", "!=", False), ("order_line_id", "!=", False), ("sent", "=", False)])
        if len(codes) > 0:
            for code in codes:
                if code.order_line_id.qty_delivered == code.order_line_id.product_uom_qty:
                    code.send_code()

    @api.one
    def send_all_possible(self):
        codes = self.env["netaddiction.specialoffer.digital_code"].search([("bonus_id", "=", self.id), ("order_id", "!=", False), ("order_line_id", "!=", False), ("sent", "=", False)])
        if len(codes) > 0:
            for code in codes:
                code.send_code()


class DigitalCode(models.Model):

    _name = "netaddiction.specialoffer.digital_code"

    code = fields.Char(string='Codice', required=True)
    order_id = fields.Many2one('sale.order', string='Ordine collegato', default=None)
    bonus_id = fields.Many2one('netaddiction.specialoffer.digital_bonus', string='offerta collegato', default=None)
    sent = fields.Boolean(string="Spedito", default=False)
    date_sent = fields.Datetime('Data spedizione')
    sent_by = fields.Many2one(comodel_name='res.users', string='Spedito da')
    order_line_id = fields.Many2one('sale.order.line', string='order line collegata', default=None)

    @api.one
    def send_code(self):
        if self.order_id:
            message = u"Il codice bonus è: <b>%s</b>" % self.code 
            message += self.bonus_id.mail_text
            message += " <br> Grazie per aver acquistato su multiplayer.com" 
            body = None
            company_mail = self.env['netaddiction.project.issue.settings.companymail'].search([("company_id", "=", self.env.user.company_id.id)])
            if company_mail:
                template = company_mail.template_email
                if template:
                    body = template.replace('[TAG_BODY]', message)
            if not body:
                body = message

            values = {
                'subject': 'BONUS DIGITALE PER PRODOTTO %s' % self.order_line_id.product_id.name,
                'body_html': body,
                'email_from': 'no-reply@multiplayer.com',
                'email_to': self.order_id.partner_id.email,
            }

            email = self.env['mail.mail'].create(values)
            try:
                email.send(raise_exception=True)
            except Exception:
                return False

            self.sent = True
            self.date_sent = fields.Datetime.now()
            self.sent_by = self.env.user.id
            return True





class DigitalProducts(models.Model):

    _inherit = 'product.product'

    code_ids = fields.Many2many('netaddiction.specialoffer.digital_bonus', 'prod_codes_rel', 'prod_id', 'code_id', 'Codici Digitali')

class DigitalOrders(models.Model):

    _inherit = 'sale.order'

    code_ids = fields.One2many('netaddiction.specialoffer.digital_code', 'order_id', string='Codici associati')
