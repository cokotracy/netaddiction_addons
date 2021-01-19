# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import date, timedelta
from odoo import api, fields, models


class ProductCategory(models.Model):

    _inherit = 'product.category'

    check_in_internal_mail = fields.Boolean()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    available_date = fields.Date(
        string="Data disponibilità"
    )

    out_date = fields.Date(
        string="Data di Uscita"
    )

    out_date_approx_type = fields.Selection(
        [('accurate', 'Preciso'),
         ('month', 'Mensile'),
         ('quarter', 'Trimestrale'),
         ('four', 'Quadrimestrale'),
         ('year', 'Annuale')],
        help="Impatta sulla vista front end\n"
        "Preciso: la data inserita è quella di uscita\n"
        "Mensile: qualsiasi data inserita prende solo il mese e l'anno"
        " (es: in uscita nel mese di Dicembre 2019)\n"
        "Trimestrale: prende l'anno e mese e calcola il trimestre"
         " (es:in uscita nel terzo trimestre 2019)\n"
        "Quadrimestrale: prende anno e mese e calcola il quadrimestre"
         " (es:in uscita nel primo quadrimestre del 2019)\n"
        "Annuale: prende solo l'anno (es: in uscita nel 2019)",
        string="Approssimazione Data",
    )

    def write(self, values):
        res = super().write(values)
        if 'sale_ok' in values.keys():
            self._mail_check_sale_ok()
        if 'visible' in values.keys():
            self._mail_check_visible()
        return res

    @api.model
    def create(self, values):
        res = super().create(values)
        if 'sale_ok' in values.keys():
            res._mail_check_sale_ok()
        if 'visible' in values.keys():
            res._mail_check_visible()
        return res

    def _mail_check_sale_ok(self):
        # Migrated from netaddiction_mail/models/product v9.0
        if self.env.context.get('skip_notification_mail', False):
            return
        user = self.env.user
        template = self.env.ref(
            'netaddiction_products.out_of_stock_product')
        template = template.sudo().with_context(lang=user.lang)
        included_categories = self.env['product.category'].search([
            ('check_in_internal_mail', '=', True), ])
        for product in self.filtered(
                lambda p: not p.sale_ok and p.categ_id in included_categories):
            template.send_mail(
                product.id, force_send=False, raise_exception=True)

    def _mail_check_visible(self):
        # Migrated from netaddiction_mail/models/product v9.0
        if self.env.context.get('skip_notification_mail', False):
            return
        user = self.env.user
        template = self.env.ref(
            'netaddiction_products.product_on_or_off')
        template = template.sudo().with_context(lang=user.lang)
        included_categories = self.env['product.category'].search([
            ('check_in_internal_mail', '=', True), ])
        for product in self.filtered(
                lambda p: p.categ_id in included_categories):
            template.send_mail(
                product.id, force_send=False, raise_exception=True)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _order = 'name, id'

    default_code = fields.Char(
        string='Internal Reference',
        compute='compute_default_code',
        search='search_default_code',
        readonly=True,
        index=True,
    )

    final_price = fields.Float(
        string="Pricelist Price",
        digits='Product Price'
    )

    special_price = fields.Float(
        string="Prezzo offerta base",
        digits='Product Price',
        default=0
    )

    qty_available_now = fields.Integer(
        compute="_get_qty_available_now",
        # search="_search_available_now",
        string="Quantità Disponibile",
        help="Quantità Disponibile Adesso (qty in possesso - qty in uscita)")

    med_inventory_value = fields.Float(
        string="Valore Medio Inventario Deivato",
        default=0,
        compute="_get_inventory_medium_value"
    )

    med_inventory_value_intax = fields.Float(
        string="Valore Medio Inventario Ivato",
        default=0,
        compute="_get_inventory_medium_value"
    )

    def _get_inventory_medium_value(self):
        for product in self:
            stock = self.env.ref('stock.stock_location_stock').id
            if product.qty_available > 0:
                quants = self.env['stock.quant'].search(
                    [
                        ('product_id', '=', product.id),
                        ('location_id', '=', stock),
                        ('company_id', '=', self.env.user.company_id.id)
                    ]
                )
                qta = 0
                value = 0
                for quant in quants:
                    qta += quant.quantity
                    value += 0 # quant.inventory_value
                val = float(value) / float(qta)
                result = product.supplier_taxes_id.compute_all(val)
                product.med_inventory_value_intax = round(
                    result['total_included'], 2)
                product.med_inventory_value = round(
                    result['total_excluded'], 2)
            else:
                product.med_inventory_value = 0

    def compute_default_code(self):
        for product in self:
            product.default_code = str(product.id)

    def search_default_code(self, operator, value):
        return [('id', operator, value)]

    def _get_qty_available_now(self):
        for product in self:
            product.qty_available_now = \
                product.qty_available - product.outgoing_qty


class SupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'

    avail_qty = fields.Float(
        string='Available Qty'
    )
