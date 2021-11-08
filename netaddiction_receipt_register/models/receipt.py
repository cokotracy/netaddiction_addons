import xlwt
from datetime import datetime
from calendar import monthrange
from ast import literal_eval

from odoo import api, fields, models
from odoo.exceptions import UserError


class ReceiptRegister(models.Model):
    _name = "receipt.register"

    date_start = fields.Datetime(string="Data Inizio")
    date_end = fields.Datetime(string="Data Fine")
    name = fields.Char(string="Nome", compute="_get_my_name")
    output_file = fields.Binary(string="File generato")
    output_filename = fields.Char(string="Nome File", compute="_get_output_filename")

    def _get_my_name(self):
        for receipt in self:
            receipt.name = f"Corrispettivi di {receipt.date_end.strftime('%B %Y')}"

    def _get_output_filename(self):
        for receipt in self:
            receipt.output_filename = f"corrispettivi_{receipt.date_end.strftime('%B_%Y')}.xls"

    def _get_delivery_picking_type_ids(self):
        params = self.env["ir.config_parameter"].sudo()
        ids = params.get_param("receipt.register.delivery_picking_type_ids")
        if not ids:
            raise UserError(
                "Non hai impostato nessuna tipologia di 'Spedizioni ai clienti/vendite' nelle impostazioni del modulo"
            )
        return literal_eval(ids)

    def _get_refund_picking_type_ids(self):
        params = self.env["ir.config_parameter"].sudo()
        ids = params.get_param("receipt.register.refund_picking_type_ids")
        if not ids:
            raise UserError("Non hai impostato nessuna tipologia di 'Resi'")
        return literal_eval(ids)

    def _create_subdivision(
        self, pickings, numberdays, month_date, check_sale_id=True, check_sale_origin=False, refund_delivery_cost=True
    ):
        pass

    def get_receipt(self):
        numberdays = monthrange(self.date_end.year, self.date_end.month)[1]
        numberdays = list(range(1, numberdays + 1))

        delivery_picking_type_ids = self._get_delivery_picking_type_ids()
        refund_picking_type_ids = self._get_refund_picking_type_ids()

        domain = [("state", "=", "done"), ("date_done", ">=", self.date_start), ("date_done", "<=", self.date_end)]

        wb = xlwt.Workbook()
        # Creo i fogli: uno per le spedizioni in uscita, uno per i resi
        delivery_sheet = wb.add_sheet("Vendite %s" % (self.date_end.strftime("%m - %Y")))
        refund_sheet = wb.add_sheet("Resi %s" % (self.date_end.strftime("%m - %Y")))

        # Cerco tutte le spedizioni in uscita
        delivery_domain = domain + [("picking_type_id.id", "in", delivery_picking_type_ids)]
        pickings = self.env["stock.picking"].search(delivery_domain)

        delivery_picks, tax_names = self.create_subdivision(pickings, numberdays, self.date_end)
        # in delivery_picks ho i dati che mi servono, fatturato e tasse divisi per giorno
        # self.create_sheet(tax_names, delivery_sheet, delivery_picks, numberdays)

        # # resi
        # refund_domain = domain + [("picking_type_id.id", "in", refund_picking_type_ids)]
        # pickings = self.env["stock.picking"].search(refund_domain)
        # refund_cost = self.env["ir.values"].search(
        #     [("name", "=", "refund_delivery_cost"), ("model", "=", "receipt.register.config.settings")]
        # )
        # if refund_cost:
        #     refund_cost = refund_cost.value
        # else:
        #     refund_cost = False
        # refund_picks, tax_names = self.create_subdivision(
        #     pickings,
        #     numberdays,
        #     month_date,
        #     check_sale_id=False,
        #     check_sale_origin=True,
        #     refund_delivery_cost=refund_cost,
        # )
        # # in refund_picks ho i dati che mi servono, fatturato e tasse divisi per giorno
        # self.create_sheet(tax_names, refund_sheet, refund_picks, numberdays)

        # fp = StringIO()
        # wb.save(fp)
        # fp.seek(0)
        # self.file = base64.b64encode(fp.read()).decode()


class ReceiptRegisterConfig(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_picking_type_ids = fields.Many2many(
        "stock.picking.type", "delivery_picking", string="Spedizioni ai clienti/vendite"
    )
    refund_picking_type_ids = fields.Many2many("stock.picking.type", "refund_picking", string="Resi")
    refund_delivery_cost = fields.Boolean(string="Contare le spese di spedizione nei resi")
    product_cod_id = fields.Many2one("product.product", string="Prodotto contrassegno")

    @api.model
    def get_values(self):
        res = super(ReceiptRegisterConfig, self).get_values()
        icp = self.env["ir.config_parameter"].sudo()
        delivery_picking_type_ids = icp.get_param("receipt.register.delivery_picking_type_ids")
        refund_picking_type_ids = icp.get_param("receipt.register.refund_picking_type_ids")
        product_cod_id = icp.get_param("receipt.register.product_cod_id")
        res.update(
            delivery_picking_type_ids=[(6, 0, literal_eval(delivery_picking_type_ids))]
            if delivery_picking_type_ids
            else False,
            refund_picking_type_ids=[(6, 0, literal_eval(refund_picking_type_ids))]
            if refund_picking_type_ids
            else False,
            product_cod_id=int(product_cod_id) or False,
        )
        return res

    @api.model
    def set_values(self):
        res = super(ReceiptRegisterConfig, self).set_values()
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("receipt.register.delivery_picking_type_ids", self.delivery_picking_type_ids.ids)
        icp.set_param("receipt.register.refund_picking_type_ids", self.refund_picking_type_ids.ids)
        icp.set_param("receipt.register.product_cod_id", self.product_cod_id.id)
        return res
