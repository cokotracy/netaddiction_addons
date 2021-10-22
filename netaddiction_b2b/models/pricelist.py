# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import io
import csv
import datetime
import base64
from ftplib import FTP
from odoo import api, fields, models, _


# TODO: Remove code after the last migration
# (the last refactoring to remove useless code)

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


# TODO: Remove useless class

class ProductPricelistCondition(models.Model):
    _name = 'pricelist.condition'
    _description = 'Pricelist Condition'


# TODO: Remove code after the last migration
# (the last refactoring to remove useless code)

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_b2b = fields.Boolean(
        string='Is a B2B'
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
            'store_fname': name,
            'type': 'binary',
            'datas': data,
            'res_model': 'product.pricelist',
            'res_field': 'last_attachment_id',
            'res_id': self.id,
            'res_name': self.name,
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
        file_content = io.BytesIO(base64.b64decode(
            self.last_attachment_id.datas))
        filename = 'Listino_Multiplayer_com_%s.csv' % \
            datetime.date.today().strftime('%Y_%m_%d')
        company = self.env.user.company_id
        ftp = FTP(
            company.pricelist_csv_ftp_host,
            company.pricelist_csv_ftp_user,
            company.pricelist_csv_ftp_password)
        for line in self.ftp_user:
            if not line.path.startswith('/'):
                path = f'/{line.path}'
            else:
                path = line.path
            ftp.cwd(path)
            current_files = [cf for cf in ftp.nlst() if cf not in ('.', '..')]
            # REmove previous files sent
            for current_file in current_files:
                ftp.delete(current_file)
            # BOOOOM! File online!
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

    def delete_all_items(self):
        for pricelist in self:
            pricelist.item_ids.unlink()


class ProductPriceItems(models.Model):
    _inherit = 'product.pricelist.item'

    b2b_real_price = fields.Float(
        compute='_get_real_price',
        string='Real Price')

    # base = fields.Selection(selection_add=[
    #     ('final_price', 'Prezzo di listino')
    #     ],
    #     string="Based On",
    #     required=True
    # )

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


class ProductPricelistDynamicDomain(models.Model):

    _inherit = 'product.pricelist.dynamic.domain'

    def _get_item_data(self):
        item_data = super()._get_item_data()
        if self.pricelist_id.is_b2b and \
                item_data.get('compute_price', '') == 'percentage':
            value = item_data.get('percent_price', 0.0)
            # For B2B pricelist, we need to remove the vat percentage.
            # We simulate a double discount to remove vat and apply
            # the real discount
            b2b_vat_percentage = 18.03
            value = (1 - (b2b_vat_percentage/100.0)) * (1 - (value/100.0))
            value = 100 - (value * 100)
            item_data['percent_price'] = round(value, 2)
        return item_data
