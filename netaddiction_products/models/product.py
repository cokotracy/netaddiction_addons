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
        readonly=True,
        store=True,
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
        search="_search_available_now",
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

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for product in res:
            product.default_code = str(product.id)
        return res

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

    def _get_qty_available_now(self):
        for product in self:
            product.qty_available_now = \
                product.qty_available - product.outgoing_qty

    # TODO this search attribute was removed, check if it's necessary
    def _search_available_now(self, operator, value):
        domain = []
        stock_move_obj = self.env['stock.move']
        product_product_obj = self.env['product.product']

        domain_for_zero = [
            ('state', 'not in', ('done', 'cancel', 'draft')),
            ('company_id', '=', self.env.user.company_id.id)
        ]
        moves_out = stock_move_obj.read_group(
            domain=domain_for_zero,
            fields=['product_id', 'product_qty'],
            groupby='product_id'
        )
        product_ids = [prod['product_id'][0] for prod in moves_out]
        products = product_product_obj.search(
            [('id', 'in', product_ids)]
        )
        # Get product ids from operator
        ids = self._get_ids_from_operator(operator, products, value)
        # Get proper domain based by value, operator and ids
        if value == 0:
            domain = self._get_domain_value_equal_to_zero(operator, ids)
        elif value > 0:
            domain = self._get_domain_value_greater_than_zero(
                operator, ids, value)
        elif value < 0:
            domain = self._get_domain_value_less_than_zero(
                operator, ids, value)
        return domain

    def _get_ids_from_operator(self, operator, products, value):
        """
        Helper method used by _search_available_now() that return a
        list of product.product ids by checking operator and value
        Args:
            operator (string): Operator used by search
            products (product.product()): Products recordset
            value (Integer): Value to search

        Returns:
            list: List of product.product ids
        """
        ids = []
        for prod in products:
            qty_available_now = prod.qty_available_now
            if operator == '<=' and qty_available_now <= value:
                ids.append(prod.id)
            elif operator == '<' and qty_available_now < value:
                ids.append(prod.id)
            elif operator == '>=' and qty_available_now < value:
                ids.append(prod.id)
            elif operator == '>' and qty_available_now <= value:
                ids.append(prod.id)
            elif operator == '=' and value >= 0 and qty_available_now != value:
                ids.append(prod.id)
            elif operator == '=' and value < 0 and qty_available_now == value:
                ids.append(prod.id)
        return ids

    def _get_domain_value_equal_to_zero(self, operator, ids):
        """
        Helper method used by _search_available_now() that return a proper
        domain by checking operator and ids records if search value == 0

        Args:
            operator (string): Operator used by search
            ids (list): List of product.product ids

        Returns:
            Odoo domain : product.product() search domain
        """
        product_product_obj = self.env['product.product']
        # Set the proper domain from operatore
        if operator == '<=':
            domain = [
                '|',
                ('qty_available', '<=', 0),
                ('id', 'in', ids)
            ]
        elif operator == '<':
            domain = [
                ('id', 'in', ids)
            ]
        elif operator == '>=':
            available = product_product_obj.search(
                [
                    ('qty_available', '>=', 0),
                    ('id', 'not in', ids)
                ]
            )
            domain = [
                ('id', 'in', available.ids)
            ]
        elif operator == '>':
            available = product_product_obj.search(
                [
                    ('qty_available', '>', 0),
                    ('id', 'not in', ids)
                ]
            )
            domain = [
                ('id', 'in', available.ids)
            ]
        elif  operator == '=':
            available = product_product_obj.search(
                [
                    ('qty_available', '=', 0),
                    ('id', 'not in', ids)
                ]
            )
            domain = [
                ('id', 'in', available.ids)
            ]
        else:
            domain = []
        return domain

    def _get_domain_value_greater_than_zero(self, operator, ids, value):
        """
        Helper method used by _search_available_now() that return a proper
        domain by checking operator and ids records if search value > 0

        Args:
            operator (string): Operator used by search
            ids (list): List of product.product ids
            value (Integer): Value to search

        Returns:
            Odoo domain : product.product() search domain
        """
        product_product_obj = self.env['product.product']
        if operator == '<=' or operator == '<':
            domain = [
                '|',
                ('qty_available', operator, value),
                ('id', 'in', ids)
            ]
        elif operator == '>=' or operator == '>':
            available = product_product_obj.search(
                [
                    ('qty_available', operator, value),
                    ('id', 'not in', ids)
                ]
            )
            domain = [
                ('id', 'in', available.ids)
            ]
        elif operator == '=':
            available = product_product_obj.search(
                [
                    ('qty_available', '=', value),
                    ('id', 'not in', ids)
                ]
            )
            domain = [
                ('id', 'in', available.ids)
            ]
        else:
            domain = []
        return domain

    def _get_domain_value_less_than_zero(self, operator, ids, value):
        """
        Helper method used by _search_available_now() that return a proper
        domain by checking operator and ids records if search value < 0

        Args:
            operator (string): Operator used by search
            ids (list): List of product.product ids
            value (Integer): Value to search

        Returns:
            Odoo domain : product.product() search domain
        """

        product_product_obj = self.env['product.product']
        if operator == '<=' or operator == '<':
            domain = [
                ('id', 'in', ids)
            ]
        elif operator == '>=' or operator == '>':
            available = product_product_obj.search(
                [
                    ('qty_available', operator, value),
                    ('id', 'not in', ids)
                ]
            )
            domain = [
                ('id', 'in', available.ids)
            ]
        elif operator == '=':
            domain = [
                ('id', 'in', ids)
            ]
        else:
            domain = []
        return domain


class SupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'

    avail_qty = fields.Float(
        string='Available Qty'
    )
