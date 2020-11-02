# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import io
import csv
import locale
import datetime
import base64
from ftplib import FTP
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PricelistFTPUser(models.Model):
    _name = 'netaddiction_pricelist_ftp_user'
    _description = 'Netaddiction Pricelist FTP User'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer'
    )

    path = fields.Char(
        string='FTP Path'
    )


class ProductPricelistCondition(models.Model):
    _name = 'pricelist.condition'
    _description = 'Pricelist Condition'

    expression = fields.Many2one(
        'netaddiction.expressions.expression',
        string='Expression'
    )

    percentage_discount = fields.Integer(
        string='Discount %'
    )

    typology = fields.Selection([
        ('discount', 'Discount'),
        ('inflation', 'Inflation')
        ],
        string='Pricelist Type',
        default='discount',
    )


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    expression = fields.Many2many(
        'pricelist.condition',
        string='Expressions'
    )

    carrier_price = fields.Float(
        string='Delivery Cost'
    )

    carrier_gratis = fields.Float(
        string='Gratis Delivery if amount greater than',
        default=0.0
    )

    last_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Last Attachment',
    )

    percent_price = fields.Float(
        string='Default % (discount)'
    )

    search_field = fields.Char(
        string='Search Products'
    )

    generate_csv_ftp = fields.Boolean(
        string='Generate Periodic CSV'
    )

    ftp_user = fields.Many2many(
        'netaddiction_pricelist_ftp_user',
        string='Customers/Paths',
    )

    @staticmethod
    def _get_csv_header():
        return ['Sku', 'Prodotto', 'Barcode', 'Quantita', 'Prezzo']

    def _get_csv_content(self, ftp=False):
        self.ensure_one()
        output = io.StringIO()
        writer = csv.writer(output)
        csv_header = self._get_csv_header()
        writer.writerow(csv_header)
        for line in self.item_ids.filtered(lambda r: r.product_id):
            price = '{:.2f}'.format(line.b2b_real_price)
            product = line.product_id
            csvdata = [
                product.id,
                product.with_context(
                    {'lang': u'it_IT', 'tz': u'Europe/Rome'}
                    ).display_name,
                product.barcode,
                line.qty_available_now,
                price]
            writer.writerow(csvdata)
        data = base64.b64encode(output.getvalue().encode())
        output.close()
        return data

    def _get_csv_data(self):
        self.ensure_one()
        data = self._get_csv_content()
        name = 'Multiplayer_com_B2B_%s.csv' % datetime.date.today()
        return {
            'name': name,
            'datas_fname': name,
            'type': 'binary',
            'datas': data
            }

    def create_csv(self):
        csv_data = self._get_csv_data()
        attachment = self.env['ir.attachment'].create(csv_data)
        self.last_attachment_id = attachment.id
        return attachment

    def send_csv_to_ftp(self):
        self.ensure_one()
        # Please, don't touch this original comment because it's too epic!
        '''
        sparo in ftp
        le cartelle le chiameremo con un nome adatto al listino
        oppure avrò una lista di utenti con la cartella associata
        ogni utente ha associata una cartella con user e password,
        se non ce l'ha associata fanculo
        '''
        if not self.last_attachment_id:
            return False
        file_content = self.last_attachment_id
        company = self.env.user.company_id
        ftp = FTP(
            company.pricelist_csv_ftp_host,
            company.pricelist_csv_ftp_user,
            company.pricelist_csv_ftp_password)
        for line in self.ftp_user:
            file_content.seek(0)
            path = '/%s' % line.path
            filename = 'Listino_Multiplayer_com_%s.csv' % \
                datetime.date.today().strftime('%Y_%m_%d')
            ftp.cwd(path)
            for current_file in ftp.nlst():
                ftp.delete(current_file)
            ftp.storbinary('STOR %s' % filename, file_content)
        return True

    def create_csv_and_send_to_ftp(self, ftp=None):
        self.ensure_one()
        self.create_csv()
        if ftp:
            self.send_csv_to_ftp()
        return True

    def get_csv(self):
        self.ensure_one()
        # Create a new CSV
        self.create_csv()
        # Show created file
        action = self.env.ref('base.action_attachment').read()[0]
        action['domain'] = [('id', '=', self.last_attachment_id.id)]
        return action

    @api.model
    def cron_create_csv(self):
        pricelist = self.sudo().search([
            ('active', '=', True),
            ('generate_csv_ftp', '=', True), ])
        for price in pricelist:
            price.create_csv_and_send_to_ftp(ftp=True)

    def _compute_price_rule(self, products_qty_partner, date=False,
                            uom_id=False):
        results = super()._compute_price_rule(
            products_qty_partner, date, uom_id)
        # Please, don't touch this original comment because it's too epic!
        '''
        potrebbe essere richiesto lo stesso da un'altra pricelist,
        se non ha il rigo corrispondente ritorna results
        sennò fai un bordello
        {295923: (9.99, False)}
        '''
        public_pricelist = self.env.user.company_id.public_pricelist_id
        if self.id == public_pricelist.id:
            return results
        item_model = self.env['product.pricelist.item']
        for product_id in results:
            real_price = results[product_id][0]
            item_id = results[product_id][1]
            if not item_id:
                continue
            item = item_model.browse(item_id)
            product = item.product_id
            percentage = item.percent_price / 100
            if item.typology == 'inflation':
                purchase_price = item.purchase_price
                percentage_price = purchase_price * percentage
                real_price = purchase_price + percentage_price
                # Price must includes taxes
                real_price = product.supplier_taxes_id.compute_all(
                    real_price)['total_included']
            else:
                percentage_price = product.final_price * percentage
                real_price = product.final_price - percentage_price
            real_price = product.special_price \
                if (product.special_price > 0 and
                    product.special_price < real_price) \
                else real_price
            real_price = product.offer_price \
                if (product.offer_price > 0 and
                    product.offer_price < real_price) \
                else real_price
            results[product_id] = (real_price, item.id)
        return results

    @api.model
    def cron_updater(self):
        pricelists = self.sudo().search([('active', '=', True)])
        pricelists.filtered(
            lambda r: r.expression).populate_item_ids_from_expression()

    def populate_item_ids_from_expression(self):
        product_model = self.env['product.product']
        item_model = self.env['product.pricelist.item']
        for pricelist in self:
            if not pricelist.expression:
                raise UserError(
                    _('Set an expression on pricelist "{name}"').format(
                        name=pricelist.name))
            pids = []
            lines = {}
            for line in pricelist.item_ids:
                pids.append(line.product_id.id)
                lines[line.product_id.id] = line
                if line.qty_available_now <= line.qty_lmit_b2b:
                    line.unlink()
            new_items = []
            for expr in pricelist.expression:
                domain = expr.expression.get_domain()
                for prod in product_model.search(domain):
                    attr = {
                        'applied_on': '0_product_variant',
                        'product_id': prod.id,
                        'compute_price': 'formula',
                        'base': 'final_price',
                        'price_discount': expr.percentage_discount,
                        'percent_price': expr.percentage_discount,
                        'typology': expr.typology,
                        }
                    if prod.id not in pids:
                        new_items.append((0, 0, attr), )
            if new_items:
                pricelist.item_ids = new_items

    def delete_all_items(self):
        for pricelist in self:
            pricelist.item_ids.unlink()


class ProductPriceItems(models.Model):
    _inherit = 'product.pricelist.item'

    b2b_real_price = fields.Float(
        compute='_get_real_price',
        string='Real Price')

    base = fields.Selection(selection_add=[
        ('final_price', 'Prezzo di listino')
        ],
        string="Based On",
        required=True
    )

    purchase_price = fields.Float(
        compute='_get_purchase_price',
        string='Purchase Price',
    )

    qty_lmit_b2b = fields.Integer(
        string='B2B Limit Qty',
        default=0
    )

    qty_available_now = fields.Integer(
        related='product_id.qty_available_now',
        string='Available Qty',
    )

    typology = fields.Selection([
        ('discount', 'Discount'),
        ('inflation', 'Inflation')
        ],
        string='Pricelist Type',
        default='discount',
    )

    def _get_purchase_price(self):
        purchase_line_model = self.env['purchase.order.line']
        for item in self:
            if not item.product_id:
                item.purchase_price = 0.0
                continue
            if item.qty_available_now > 0:
                item.purchase_price = item.product_id.med_inventory_value
            else:
                po = purchase_line_model.search(
                    [('product_id', '=', item.product_id.id)],
                    order='create_date desc',
                    limit=1)
                if po:
                    item.purchase_price = po.price_unit
                else:
                    price = 0
                    num = 0
                    for sup in item.product_id.seller_ids:
                        num += 1
                        price += sup.price
                    num = num if num != 0 else 1
                    item.purchase_price = price / num

    def _get_real_price(self):
        for item in self:
            if not item.product_id:
                item.b2b_real_price = 0.0
                continue
            price = item.pricelist_id.price_rule_get(item.product_id.id, 1)
            try:
                prid = item.pricelist_id.id
                item.b2b_real_price = item.product_id.taxes_id.compute_all(
                    price[item.pricelist_id.id][0])['total_excluded']
            except:
                item.b2b_real_price = 0.0
