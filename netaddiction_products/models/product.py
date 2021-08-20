# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import date, timedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class ProductCategory(models.Model):

    _inherit = 'product.category'

    check_in_internal_mail = fields.Boolean()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    available_date = fields.Date(
        string="Data disponibilità"
    )

    type = fields.Selection(
        default='product',
    )

    company_id = fields.Many2one(
        default=lambda self: self.env.user.company_id
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

    detax_price = fields.Float(
        string="Prezzo di vendita deivato",
        compute="_get_visual_price",
        digits='Product Price',
    )

    intax_price = fields.Float(
        string="Prezzo di vendita Ivato",
        compute="_get_visual_price",
        digits='Product Price',
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

    visible = fields.Boolean(
        string="Visibile",
        default=True,
        )

    qty_available_now = fields.Integer(
        compute="_get_qty_available_now",
        search="_search_available_now",
        string="Quantita' Disponibile Adesso",
        help="Quantita' Disponibile Adesso (qty in possesso - qty in uscita)")

    qty_sum_suppliers = fields.Integer(
        string="Quantità dei fornitori",
        compute="_get_qty_suppliers",
        help="Somma delle quantità dei fornitori"
    )

    qty_single_order = fields.Integer(
        string="Quantità massima ordinabile",
        help="Quantità massima ordinabile per singolo ordine/cliente"
    )

    qty_limit = fields.Integer(
        string="Quantità limite",
        help="Imposta la quantità limite prodotto"
             " (qty disponibile == qty_limit accade Azione)"
        )

    limit_action = fields.Selection(
        selection=[
           ('nothing', 'Nessuna Azione'),
           ('no_purchasable', 'Non vendibile'),
           ('deactive', 'Invisibile e non vendibile')
        ],
        string="Azione limite",
        help="Se qty_limit impostata decide cosa fare al raggiungimento"
             " di tale qty",
    )

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('average', 'Average Price'),
        ('real', 'Real Price')],
        string="Metodo Determinazioni costi",
        default="real",
        required=True,
    )

    property_valuation = fields.Selection([
        ('manual_periodic', 'Periodic (manual)'),
        ('real_time', 'Perpetual (automated)')],
        string="Valorizzazione Inventario",
        default="real_time",
        required=True,
    )

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

    image_ids = fields.Many2many(
        'ir.attachment',
        'product_image_rel',
        'product_id',
        'attachment_id',
        string='Immagini'
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for product in res:
            product.default_code = str(product.id)
        return res

    def _get_inventory_medium_value(self):
        stock = self.env.ref('stock.stock_location_stock').id
        quant_model = self.env['stock.quant']
        for product in self:
            if product.qty_available > 0:
                quants = quant_model.search(
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
                    value += 0.0  # quant.inventory_value
                if qta:
                    val = float(value) / float(qta)
                else:
                    val = 0.0
                result = product.supplier_taxes_id.compute_all(val)
                product.med_inventory_value_intax = round(
                    result.get('total_included', 0.0), 2)
                product.med_inventory_value = round(
                    result.get('total_excluded', 0.0), 2)
            else:
                product.med_inventory_value_intax = 0.0
                product.med_inventory_value = 0.0

    def _get_qty_available_now(self):
        for product in self:
            product.qty_available_now = \
                product.qty_available - product.outgoing_qty

    def _get_qty_suppliers(self):
        for item in self:
            item.qty_sum_suppliers = sum(
                [int(sup.avail_qty) for sup in self.seller_ids]
            )
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
        elif operator == '=':
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

    @api.depends('final_price', 'special_price')
    def _get_visual_price(self):
        for product in self:
            result = product.taxes_id.compute_all(product.list_price)
            product.detax_price = result.get('total_excluded', 0.0)
            product.intax_price = result.get('total_included', 0.0)

    def _compute_product_lst_price(self):
        # Ehy Odoo, are you trying to show a price? Ahahahahahaha
        # Pfffff. Misguided idealist! Get my data and shut up!
        super()._compute_product_lst_price()
        # Force Odoo to show the pricelist data as list price
        item_model = self.env['product.pricelist.item'].sudo()
        for product in self:
            price = product.lst_price
            item = item_model.search([
                ('applied_on', '=', '0_product_variant'),
                ('product_id', '=', product.id),
                ], limit=1)
            if item:
                price = item.fixed_price
            product.lst_price = price


class SupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'

    avail_qty = fields.Float(
        string='Available Qty'
    )

    detax_margin = fields.Float(
        string="Margine iva esclusa",
        compute="_calculate_margin_info"
    )

    def _calculate_margin_info(self):
        for item in self:
            prod = item.product_id
            sup_price = prod.supplier_taxes_id.compute_all(item.price)
            # FIXME The following line uses offer_price, which is a custom
            # field from netaddiction.special_offers. Since we haven't migrated
            # that module, this field is not available anymore. Nevertheless
            # we should better evaluate this change, as our client may expect
            # to find this margin information calculated the old way.
            # sale_price = prod.offer_price or prod.list_price
            sale_price = prod.list_price
            prod_price = prod.taxes_id.compute_all(sale_price)

            item.detax_margin = prod_price['total_excluded'] \
                - sup_price['total_excluded']


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'

    @api.constrains("product_id")
    def _unique_product(self):
        for item in self:
            if item.product_id and self.search([
                    ('product_id', '=', item.product_id.id),
                    ('id', '!=', item.id),
                    ]):
                raise ValidationError(_(
                    "Impossibile to create more than one pricelist rule"
                    "for product %s"
                    ) % item.product_id.name_get()[0][1])
