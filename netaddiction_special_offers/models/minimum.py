# -*- coding: utf-8 -*-

# TODO: This whole class has been disabled in __init__.py because we will
# handle the minimo garantito by creating a custom sale coupon when the
# product is shipped and in case the product's price has changed since it
# was bought


from openerp.exceptions import Warning
from openerp import models, fields, api
import datetime

class Orders(models.Model):
    _inherit = "sale.order"
    is_guaranteed_minimum = fields.Boolean(string="é minimo garantito?", default=False)
    is_guaranteed_minimum_refund = fields.Boolean(string="é rimborsato il minimo garantito?", default=False)

    @api.one
    def guaranteed_minimum_restore(self):
        """
        per i clienti che chiedono il rimborso,
        crea una nota di credito pari al valore della differenza tra il loro ordine e quello in minimum
        """
        val = 0
        pids = []
        ex_values = {}
        if self.is_guaranteed_minimum_refund:
            raise Warning("L'ordine è già stato Rimborsato per il minimo garantito")

        for line in self.order_line:
            if line.guaranteed_minimum_value > 0:
                val += line.guaranteed_minimum_value
                pids.append(line.product_id.id)
                ex_values[line.product_id.id] = line.guaranteed_minimum_value

        if self.partner_id.total_gift > float(val):
            self.partner_id.sudo().remove_gift_value(val)
            for inv in self.sudo().invoice_ids:
                for il in inv.sudo().invoice_line_ids:
                    if il.sudo().product_id.id in pids:
                        ref = inv.sudo().refund(datetime.datetime.now(), datetime.datetime.now(), 'Rimborso Minimo Garantito')
                        for tl in ref.sudo().tax_line_ids:
                            tl.sudo().unlink()
                        for line in ref.sudo().invoice_line_ids:
                            if line.sudo().product_id.id not in pids:
                                line.sudo().unlink()
                            else:
                                line.sudo().price_unit = ex_values[line.product_id.id]
                        ref.sudo().compute_taxes()
                inv.sudo().compute_taxes()
            self.is_guaranteed_minimum_refund = True
        else:
            raise Warning("il cliente ha già usato i gift di rimborso per il minimo garantito. Non puoi rimborsare.")

class OrdersLines(models.Model):
    _inherit = "sale.order.line"
    guaranteed_minimum_value = fields.Float(string="Valore sconto minimo garantito", default=0)

class Products(models.Model):
    _inherit = "product.product"

    @api.multi
    @api.constrains('final_price', 'special_price')
    def _guaranteed_minimum(self):
        """
        Suggerimento:
        se il prodotto ha data di uscita maggiore di oggi tecnicamente posso prendere tutte le vendite che sono a lui collegate
        (c'è il campo)
        se il prezzo di questa riga è maggiore allora lo metto nel listone
        """
        if self.out_date:
            out_date = datetime.datetime.strptime(self.out_date, '%Y-%m-%d')
            if out_date > datetime.datetime.now():
                for product in self:
                    picks = self.env['stock.picking'].sudo().search([('move_lines.product_id', '=', product.id), ('state', '=', 'confirmed')])
                    lines = []
                    for pick in picks:
                        for line in pick.sale_id.order_line:
                            if line.product_id.id == product.id and line.price_unit > product.list_price:
                                lines.append(line.id)
                    if len(lines) > 0:
                        result = self.env['netaddiction.guaranteed.minimum'].sudo().search([('state', '=', 'draft'), ('product_id', '=', product.id)])
                        if result:
                            result.sudo().write({'order_line_ids': [(6, False, lines)]})
                        else:
                            attr = {
                                'name': 'Cambio Prezzo %s' % product.display_name,
                                'date_change': datetime.date.today(),
                                'created_user_id': self.env.user.id,
                                'order_line_ids': [(6, False, lines)],
                                'company_id': self.env.user.company_id.id,
                                'product_id': product.id,
                                'new_product_price': product.list_price,
                                'state': 'draft'
                            }
                            self.env['netaddiction.guaranteed.minimum'].sudo().create(attr)

class GuaranteedMinimum(models.Model):
    _name = "netaddiction.guaranteed.minimum"

    name = fields.Char(string='Nome')
    order_line_ids = fields.Many2many(string='Linee Ordine', comodel_name="sale.order.line")
    created_user_id = fields.Many2one(string='Utente creatore', comodel_name="res.users")
    date_change = fields.Date(string="Data Cambio")
    company_id = fields.Many2one('res.company', string='Azienda', default=lambda self: self.env['res.company']._company_default_get('account.account'))
    product_id = fields.Many2one(string="Prodotto", comodel_name="product.product")
    state = fields.Selection(string="Stato", selection=[('draft', 'Nuovo'), ('done', 'Convalidato')], default="draft")
    new_product_price = fields.Float(string="Nuovo prezzo minimo garantito", default=0)

    @api.one
    def convalidate_change_price(self):
        """
        Aggiorno il totale dell'ordine

        Se ci sono gift come mi comporto?
            se il gift era totale allora tolgo la differenza e la rimetto come gift rimborso al cliente
        Devo ricalcolare il totale dell'ordine, non usare la funzione ma ricalcola il totale dalla somma delle order_line - gift_discount

        Se contrassegno non ci sono problemi, cambio il pagamento e la fattura
        Se paypal o bonifico:
            lascio invariati i pagamenti e le fatture e aggiungo un gift rimboso al cliente
        Se carta di credito:
            se non è pagato allora cambio il pagamento e la fattura
        """
        contrassegno = self.env.ref('netaddiction_payments.contrassegno_journal').id
        cc = self.env.ref('netaddiction_payments.cc_journal').id
        paypal = self.env.ref('netaddiction_payments.paypal_journal').id
        sofort = self.env.ref('netaddiction_payments.sofort_journal').id
        bonifico = self.env.ref('netaddiction_payments.allowance_journal').id
        zero = self.env.ref('netaddiction_payments.zeropay_journal').id
        payments = {
            contrassegno: ('contrassegno', 'change'),
            cc: ('cc', 'change'),
            paypal: ('paypal', 'no_change'),
            sofort: ('sofort', 'no_change'),
            bonifico: ('bonifico', 'no_change'),
            zero: ('zero', 'no_change')
        }
        for line in self.order_line_ids:
            correct_payment = False
            for pick in line.order_id.picking_ids:
                for move in pick.move_lines:
                    if move.product_id.id == self.product_id.id:
                        correct_payment = pick.payment_id
            if payments[line.order_id.payment_method_id.id][1] == 'change':
                # aggiorna i pagamenti sulle psedizioni
                if correct_payment.state == 'draft':
                    self.change_price(line, correct_payment)
            else:
                self.no_change_price(line)
        self.state = 'done'

    @api.model
    def change_price(self, line, payment):
        zero = self.env.ref('netaddiction_payments.zeropay_journal').id
        gift = self.env.ref('netaddiction_customer.product_gift').id
        diff = line.price_unit - self.new_product_price
        amount_diff = line.order_id.amount_total - (diff * line.product_uom_qty)
        message = 'Cambio Prezzo per minimo Garantito:\n %s \n' % line.product_id.display_name
        if amount_diff <= 0:
            # problemi forse con delle eccezioni o varie testa e controlla
            line.sudo().write({'price_unit': self.new_product_price})
            line.order_id.sudo().write({'gift_discount': line.order_id.gift_discount - abs(amount_diff)})
            line.order_id.sudo().write({'payment_method_id': zero})
            payment.sudo().unlink()
            for inv in line.order_id.invoice_ids:
                for inv_line in inv.invoice_line_ids:
                    if inv_line.product_id.id == self.product_id.id:
                        inv_line.price_unit = self.new_product_price
                    if inv_line.product_id.id == gift:
                        inv_line.price_unit = inv_line.price_unit + abs(amount_diff)
                inv.sudo().compute_taxes()
                inv.sudo().residual = inv.sudo().amount_total
            line.order_id.partner_id.sudo().add_gift_value(abs(amount_diff), 'Rimborso')
            line.order_id.sudo()._amount_all()
            message += 'Ordine messo in costo zero, gift assegnato %s' % abs(amount_diff)
        else:
            line.sudo().write({'price_unit': self.new_product_price})
            payment.sudo().write({'amount': payment.sudo().amount - (diff * line.sudo().product_uom_qty)})
            for inv in line.order_id.invoice_ids:
                for inv_line in inv.invoice_line_ids:
                    if inv_line.product_id.id == self.product_id.id:
                        inv_line.sudo().write({'price_unit': self.new_product_price})
                        inv.sudo().compute_taxes()
                        inv.sudo().residual = inv.sudo().amount_total
        attr = {
            'subtype_id': 1,
            'res_id': line.order_id.id,
            'body': message,
            'model': 'sale.order',
            'author_id': self.env.user.partner_id.id,
            'message_type': 'comment',
        }
        self.env['mail.message'].create(attr)

    @api.model
    def no_change_price(self, line):
        # qua non devo cambiare nulla, do il gift come rimborso al cliente e flaggo l'ordine e metto la differenza nella order line
        diff = line.price_unit - self.new_product_price
        line.order_id.sudo().write({'is_guaranteed_minimum': True})
        line.sudo().write({'guaranteed_minimum_value': (diff * line.product_uom_qty)})

        line.order_id.partner_id.sudo().add_gift_value(diff * line.product_uom_qty, 'Rimborso')
        message = 'Cambio Prezzo per minimo Garantito:\n %s \n gift assegnato %s' % (line.product_id.display_name, diff * line.product_uom_qty)
        attr = {
            'subtype_id': 1,
            'res_id': line.order_id.id,
            'body': message,
            'model': 'sale.order',
            'author_id': self.env.user.partner_id.id,
            'message_type': 'comment',
        }
        self.env['mail.message'].create(attr)
