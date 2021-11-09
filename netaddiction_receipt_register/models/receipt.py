import base64
import string
from ast import literal_eval
from calendar import monthrange
from collections import OrderedDict
from datetime import datetime
from io import BytesIO

import xlwt
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
            receipt.output_filename = f"corrispettivi_{receipt.date_end.strftime('%B_%Y').lower()}.xls"

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

    def _get_refund_delivery_cost(self):
        params = self.env["ir.config_parameter"].sudo()
        return params.get_param("receipt.register.refund_delivery_cost")

    def _get_product_cod_id(self):
        params = self.env["ir.config_parameter"].sudo()
        id = params.get_param("receipt.register.product_cod_id")
        if not id:
            raise UserError("Non hai impostato il prodotto di tipo 'Contrassegno'")
        return int(id)

    def _create_subdivision(
        self, pickings, numberdays, month_date, check_sale_id=True, check_sale_origin=False, refund_delivery_cost=True
    ):
        delivery_picks = {}
        tax_names = []
        multidelivery = False

        for i in numberdays:
            delivery_picks[month_date.replace(day=i).strftime("%Y-%m-%d")] = {}
        delivery_picks = OrderedDict(sorted(delivery_picks.items()))

        for pick in pickings:
            date_done = pick.date_done.strftime("%Y-%m-%d")

            if check_sale_id:
                if pick.sale_id:
                    # if it has an associated sale order we suppose it is a movement for sales
                    # group by day and fee
                    for line in pick.move_lines:
                        tax = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                        if not tax:
                            delivery_picks[date_done][line.product_id.taxes_id.name] = {}
                            delivery_picks[date_done][line.product_id.taxes_id.name][
                                "value"
                            ] = line.sale_line_id.price_total
                            delivery_picks[date_done][line.product_id.taxes_id.name][
                                "tax_value"
                            ] = line.sale_line_id.price_tax
                        else:
                            delivery_picks[date_done][line.product_id.taxes_id.name][
                                "value"
                            ] += line.sale_line_id.price_total
                            delivery_picks[date_done][line.product_id.taxes_id.name][
                                "tax_value"
                            ] += line.sale_line_id.price_tax

                        if line.product_id.taxes_id.name not in tax_names:
                            tax_names.append(line.product_id.taxes_id.name)
            else:
                # group by day and fee
                for line in pick.move_lines:
                    if check_sale_origin:
                        try:
                            origin = self.env["sale.order"].search([("name", "=", pick.origin)]).id
                        except Exception:
                            origin = False
                        if origin:
                            move = self.env["stock.move"].search(
                                [
                                    ("procurement_id.sale_line_id.order_id.id", "=", origin),
                                    ("product_id", "=", line.product_id.id),
                                ]
                            )
                            if len(move) > 0:
                                line = move[0]

                    tax = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                    if not tax:
                        delivery_picks[date_done][line.product_id.taxes_id.name] = {}
                        delivery_picks[date_done][line.product_id.taxes_id.name][
                            "value"
                        ] = line.sale_line_id.price_total
                        delivery_picks[date_done][line.product_id.taxes_id.name][
                            "tax_value"
                        ] = line.sale_line_id.price_tax
                    else:
                        delivery_picks[date_done][line.product_id.taxes_id.name][
                            "value"
                        ] += line.sale_line_id.price_total
                        delivery_picks[date_done][line.product_id.taxes_id.name][
                            "tax_value"
                        ] += line.sale_line_id.price_tax

                    if line.product_id.taxes_id.name not in tax_names:
                        tax_names.append(line.product_id.taxes_id.name)
            if refund_delivery_cost:
                carrier_price = 0
                if multidelivery and pick.carrier_price > 0:
                    carrier_price = pick.carrier_price
                else:
                    origin = pick.sale_id
                    if check_sale_origin:
                        try:
                            origin = self.env["sale.order"].search([("name", "=", pick.origin)])
                        except Exception:
                            origin = False
                    if origin:
                        for line in origin.order_line:
                            if line.is_delivery:
                                carrier_price = line.price_total

                del_pick = delivery_picks[date_done].get(pick.carrier_id.product_id.taxes_id.name, False)
                if del_pick:
                    delivery_picks[date_done][pick.carrier_id.product_id.taxes_id.name]["value"] += carrier_price
                    delivery_picks[date_done][pick.carrier_id.product_id.taxes_id.name][
                        "tax_value"
                    ] += pick.carrier_id.product_id.taxes_id.compute_all(carrier_price)["taxes"][0]["amount"]

                # cash on delivery charges
                cod_product_id = self._get_product_cod_id()
                origin = pick.sale_id
                if check_sale_origin:
                    try:
                        origin = self.env["sale.order"].search([("name", "=", pick.origin)])
                    except Exception:
                        origin = False
                if origin:
                    for line in origin.order_line:
                        if line.product_id.id == cod_product_id:
                            del_pick = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                            if del_pick:
                                delivery_picks[date_done][line.product_id.taxes_id.name]["value"] += line.price_total
                                delivery_picks[date_done][line.product_id.taxes_id.name]["tax_value"] += line.price_tax

        return delivery_picks, tax_names

    def _create_sheet(self, tax_names, delivery_sheet, delivery_picks, numberdays):
        # excel styles
        headStyle = xlwt.easyxf("font: name Arial, color-index black, bold on")
        totalStyle = xlwt.easyxf("font: name Arial, color-index green, bold on")
        numStyle = xlwt.easyxf("font: name Arial, color-index black", num_format_str="#,##0.00")
        dateStyle = xlwt.easyxf("font: name Arial, color-index red, bold on", num_format_str="DD-MM-YYYY")

        position_tax = {}
        # n is the horizontal position in the sheet, we leave some spaces to make it readable
        n = 1

        for tax_name in tax_names:
            delivery_sheet.write(0, n, f"Fatturato {tax_name}", headStyle)
            position_tax[tax_name] = [n]
            n += 1
            delivery_sheet.write(0, n, f"Tasse {tax_name}", headStyle)
            position_tax[tax_name].append(n)
            n += 2

        total_horizontal = []
        delivery_sheet.write(0, n, "Totale Fatturato", totalStyle)
        total_horizontal.append(n)
        n += 1
        delivery_sheet.write(0, n, "Totale Tasse", totalStyle)
        total_horizontal.append(n)

        # write data
        n = 1
        for line in delivery_picks:
            delivery_sheet.write(n, 0, line, dateStyle)
            for tax_name in tax_names:
                res = delivery_picks[line].get(tax_name, False)
                index = position_tax.get(tax_name, False)

                if res:
                    delivery_sheet.write(n, index[0], res["value"], numStyle)
                    delivery_sheet.write(n, index[1], res["tax_value"], numStyle)
                else:
                    delivery_sheet.write(n, index[0], 0, numStyle)
                    delivery_sheet.write(n, index[1], 0, numStyle)
            n += 1

        # put the totals, first those on column then those on row
        total_index = len(delivery_picks) + 2

        delivery_sheet.write(total_index, 0, "Totale", totalStyle)

        letters = []
        for x, y in zip(range(0, 26), string.ascii_lowercase):
            letters.append(y)

        horizontal = {0: [], 1: []}
        for tax_name in tax_names:
            index = position_tax.get(tax_name, False)
            delivery_sheet.write(
                total_index,
                index[0],
                xlwt.Formula(f"SUM({letters[index[0]].upper()}1:{letters[index[0]].upper()}{total_index - 1})"),
                totalStyle,
            )
            delivery_sheet.write(
                total_index,
                index[1],
                xlwt.Formula(f"SUM({letters[index[1]].upper()}1:{letters[index[1]].upper()}{total_index - 1})"),
                totalStyle,
            )
            horizontal[0].append(letters[index[0]].upper())
            horizontal[1].append(letters[index[1]].upper())

        for i in numberdays:
            try:
                delivery_sheet.write(
                    i,
                    total_horizontal[0],
                    xlwt.Formula(f"SUM({horizontal[0][0]}{i + 1};{horizontal[0][1]}{i + 1})"),
                )
                delivery_sheet.write(
                    i,
                    total_horizontal[1],
                    xlwt.Formula(f"SUM({horizontal[1][0]}{i + 1};{horizontal[1][1]}{i + 1})"),
                )
            except IndexError:
                delivery_sheet.write(i, total_horizontal[0], xlwt.Formula(f"SUM({horizontal[0][0]}{i + 1})"))
                delivery_sheet.write(i, total_horizontal[1], xlwt.Formula(f"SUM({horizontal[1][0]}{i + 1})"))

    def get_receipt(self):
        numberdays = monthrange(self.date_end.year, self.date_end.month)[1]
        numberdays = list(range(1, numberdays + 1))

        delivery_picking_type_ids = self._get_delivery_picking_type_ids()
        refund_picking_type_ids = self._get_refund_picking_type_ids()

        domain = [("state", "=", "done"), ("date_done", ">=", self.date_start), ("date_done", "<=", self.date_end)]

        wb = xlwt.Workbook()
        # Create sheets: one for outgoing shipments, one for returns
        delivery_sheet = wb.add_sheet("Vendite %s" % (self.date_end.strftime("%m - %Y")))
        refund_sheet = wb.add_sheet("Resi %s" % (self.date_end.strftime("%m - %Y")))

        # Search all outgoing shipments
        delivery_domain = domain + [("picking_type_id.id", "in", delivery_picking_type_ids)]
        pickings = self.env["stock.picking"].search(delivery_domain)

        delivery_picks, tax_names = self._create_subdivision(pickings, numberdays, self.date_end)
        # delivery_picks: sales and taxes divided by day
        self._create_sheet(tax_names, delivery_sheet, delivery_picks, numberdays)

        # # returns
        # refund_domain = domain + [("picking_type_id.id", "in", refund_picking_type_ids)]
        # pickings = self.env["stock.picking"].search(refund_domain)

        # refund_picks, tax_names = self._create_subdivision(
        #     pickings,
        #     numberdays,
        #     self.date_end,
        #     check_sale_id=False,
        #     check_sale_origin=True,
        #     refund_delivery_cost=self._get_refund_delivery_cost(),
        # )
        # # refund_picks: sales and taxes divided by day
        # self._create_sheet(tax_names, refund_sheet, refund_picks, numberdays)

        # generate and save the file
        fp = BytesIO()
        wb.save(fp)
        self.output_file = base64.b64encode(fp.getvalue())
        fp.close()


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
