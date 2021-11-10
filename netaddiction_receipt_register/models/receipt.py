import base64
import string
from ast import literal_eval
from calendar import monthrange
from collections import OrderedDict
from datetime import date, datetime
from io import BytesIO

import xlwt
from odoo import api, fields, models
from odoo.exceptions import UserError


class ReceiptRegister(models.Model):
    _name = "receipt.register"

    date_start = fields.Datetime(string="Data Inizio")
    date_end = fields.Datetime(string="Data Fine")
    output_file = fields.Binary(string="File generato")
    output_filename = fields.Char(string="Nome File", compute="_compute_output_filename")

    def name_get(self):
        res = []
        for receipt in self:
            try:
                name = f"Corrispettivi di {receipt.date_end.strftime('%B %Y')}"
            except Exception:
                name = "Corrispettivo non valido"
            res.append((receipt.id, name))
        return res

    def _compute_output_filename(self):
        for receipt in self:
            receipt.output_filename = f"corrispettivi_{receipt.date_end.strftime('%B_%Y').lower()}.xls"

    def get_delivery_picking_type_ids(self):
        params = self.env["ir.config_parameter"].sudo()
        ids = params.get_param("receipt.register.delivery_picking_type_ids")
        if not ids:
            raise UserError(
                "Non hai impostato nessuna tipologia di 'Spedizioni ai clienti/vendite' nelle impostazioni del modulo"
            )
        return literal_eval(ids)

    def get_refund_picking_type_ids(self):
        params = self.env["ir.config_parameter"].sudo()
        ids = params.get_param("receipt.register.refund_picking_type_ids")
        if not ids:
            raise UserError("Non hai impostato nessuna tipologia di 'Resi'")
        return literal_eval(ids)

    def get_refund_delivery_cost(self):
        params = self.env["ir.config_parameter"].sudo()
        return params.get_param("receipt.register.refund_delivery_cost")

    def get_product_cod_id(self):
        params = self.env["ir.config_parameter"].sudo()
        id = params.get_param("receipt.register.product_cod_id")
        if not id:
            raise UserError("Non hai impostato il prodotto di tipo 'Contrassegno'")
        return int(id)

    def get_tax_income_id(self):
        params = self.env["ir.config_parameter"].sudo()
        id = params.get_param("receipt.register.tax_income_id")
        if not id:
            raise UserError("Non hai impostato l'imposta")
        return int(id)

    def get_edizioni_brand_id(self):
        params = self.env["ir.config_parameter"].sudo()
        id = params.get_param("receipt.register.edizioni_brand_id")
        if not id:
            raise UserError("Non hai impostato il brand collegato a Multiplayer Edizioni")
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
                            delivery_picks[date_done][line.product_id.taxes_id.name] = {
                                "value": line.sale_line_id.price_total,
                                "tax_value": line.sale_line_id.price_tax,
                            }
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
                    if check_sale_origin and not pick.sale_id:
                        try:
                            origin = self.env["sale.order"].search([("name", "=", pick.origin)]).id
                        except Exception:
                            origin = False
                        if origin:
                            move = self.env["stock.move"].search(
                                [
                                    ("sale_line_id.order_id.id", "=", origin),
                                    ("product_id", "=", line.product_id.id),
                                ],
                                limit=1,
                            )
                            if move:
                                line = move

                    tax = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                    if not tax:
                        delivery_picks[date_done][line.product_id.taxes_id.name] = {
                            "value": line.sale_line_id.price_total,
                            "tax_value": line.sale_line_id.price_tax,
                        }

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
                    if check_sale_origin and not pick.sale_id:
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
                cod_product_id = self.get_product_cod_id()
                if check_sale_origin and not pick.sale_id:
                    try:
                        origin = self.env["sale.order"].search([("name", "=", pick.origin)])
                    except Exception:
                        origin = False
                    if origin:
                        for line in origin.order_line:
                            if line.product_id.id == cod_product_id:
                                del_pick = delivery_picks[date_done].get(line.product_id.taxes_id.name, False)
                                if del_pick:
                                    delivery_picks[date_done][line.product_id.taxes_id.name][
                                        "value"
                                    ] += line.price_total
                                    delivery_picks[date_done][line.product_id.taxes_id.name][
                                        "tax_value"
                                    ] += line.price_tax

        return delivery_picks, tax_names

    def _create_sheet(self, tax_names, sheet, picks, numberdays):
        # excel styles
        headStyle = xlwt.easyxf("font: name Arial, color-index black, bold on")
        totalStyle = xlwt.easyxf("font: name Arial, color-index green, bold on")
        numStyle = xlwt.easyxf("font: name Arial, color-index black", num_format_str="#,##0.00")
        dateStyle = xlwt.easyxf("font: name Arial, color-index red, bold on", num_format_str="DD-MM-YYYY")

        position_tax = {}
        # n is the horizontal position in the sheet, we leave some spaces to make it readable
        n = 1

        for tax_name in tax_names:
            sheet.write(0, n, f"Fatturato {tax_name}", headStyle)
            position_tax[tax_name] = [n]
            n += 1
            sheet.write(0, n, f"Tasse {tax_name}", headStyle)
            position_tax[tax_name].append(n)
            n += 2

        total_horizontal = []
        sheet.write(0, n, "Totale Fatturato", totalStyle)
        total_horizontal.append(n)
        n += 1
        sheet.write(0, n, "Totale Tasse", totalStyle)
        total_horizontal.append(n)

        # write data
        n = 1
        for line in picks:
            sheet.write(n, 0, line, dateStyle)
            for tax_name in tax_names:
                res = picks[line].get(tax_name, False)
                index = position_tax.get(tax_name, False)

                if res:
                    sheet.write(n, index[0], res["value"], numStyle)
                    sheet.write(n, index[1], res["tax_value"], numStyle)
                else:
                    sheet.write(n, index[0], 0, numStyle)
                    sheet.write(n, index[1], 0, numStyle)
            n += 1

        # put the totals, first those on column then those on row
        total_index = len(picks) + 2

        sheet.write(total_index, 0, "Totale", totalStyle)

        letters = []
        for x, y in zip(range(0, 26), string.ascii_lowercase):
            letters.append(y)

        horizontal = {0: [], 1: []}
        for tax_name in tax_names:
            index = position_tax.get(tax_name, False)
            sheet.write(
                total_index,
                index[0],
                xlwt.Formula(f"SUM({letters[index[0]].upper()}1:{letters[index[0]].upper()}{total_index - 1})"),
                totalStyle,
            )
            sheet.write(
                total_index,
                index[1],
                xlwt.Formula(f"SUM({letters[index[1]].upper()}1:{letters[index[1]].upper()}{total_index - 1})"),
                totalStyle,
            )
            horizontal[0].append(letters[index[0]].upper())
            horizontal[1].append(letters[index[1]].upper())

        for i in numberdays:
            try:
                sheet.write(
                    i,
                    total_horizontal[0],
                    xlwt.Formula(f"SUM({horizontal[0][0]}{i + 1};{horizontal[0][1]}{i + 1})"),
                )
                sheet.write(
                    i,
                    total_horizontal[1],
                    xlwt.Formula(f"SUM({horizontal[1][0]}{i + 1};{horizontal[1][1]}{i + 1})"),
                )
            except IndexError:
                sheet.write(i, total_horizontal[0], xlwt.Formula(f"SUM({horizontal[0][0]}{i + 1})"))
                sheet.write(i, total_horizontal[1], xlwt.Formula(f"SUM({horizontal[1][0]}{i + 1})"))

    def get_receipt(self):
        numberdays = monthrange(self.date_end.year, self.date_end.month)[1]
        numberdays = list(range(1, numberdays + 1))

        delivery_picking_type_ids = self.get_delivery_picking_type_ids()
        refund_picking_type_ids = self.get_refund_picking_type_ids()

        domain = [("state", "=", "done"), ("date_done", ">=", self.date_start), ("date_done", "<=", self.date_end)]

        wb = xlwt.Workbook()
        # Create sheets: one for outgoing shipments, one for returns
        delivery_sheet = wb.add_sheet("Vendite %s" % (self.date_end.strftime("%m - %Y")))
        refund_sheet = wb.add_sheet("Resi %s" % (self.date_end.strftime("%m - %Y")))

        # Search all outgoing shipments
        delivery_domain = domain + [("picking_type_id.id", "in", delivery_picking_type_ids)]
        pickings = self.env["stock.picking"].search(delivery_domain)

        if pickings:
            delivery_picks, tax_names = self._create_subdivision(pickings, numberdays, self.date_end)
            # delivery_picks: sales and taxes divided by day
            self._create_sheet(tax_names, delivery_sheet, delivery_picks, numberdays)

        # returns
        refund_domain = domain + [("picking_type_id.id", "in", refund_picking_type_ids)]
        pickings = self.env["stock.picking"].search(refund_domain)

        if pickings:
            refund_picks, tax_names = self._create_subdivision(
                pickings,
                numberdays,
                self.date_end,
                check_sale_id=False,
                check_sale_origin=True,
                refund_delivery_cost=self.get_refund_delivery_cost(),
            )
            # refund_picks: sales and taxes divided by day
            self._create_sheet(tax_names, refund_sheet, refund_picks, numberdays)

        # generate and save the file
        fp = BytesIO()
        wb.save(fp)
        self.output_file = base64.b64encode(fp.getvalue())
        fp.close()


class ReceiptRegisterPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def get_picking_from_date(self, year, month):
        results = {"done": [], "refund": []}

        tax_income_id = self.env["receipt.register"].get_tax_income_id()
        tax_income_id = self.env["account.tax"].browse(tax_income_id)
        delivery_picking_type_ids = self.env["receipt.register"].get_delivery_picking_type_ids()
        refund_picking_type_ids = self.env["receipt.register"].get_refund_picking_type_ids()
        edizioni_brand_id = self.env["receipt.register"].get_edizioni_brand_id()

        last = monthrange(year, month)
        date_from = datetime(year, month, 1)
        date_to = date_from.replace(day=last[1], hour=23, minute=59, second=59)

        pickings = self.search(
            [
                ("date_done", ">=", date_from),
                ("date_done", "<=", date_to),
                ("picking_type_id", "in", delivery_picking_type_ids),
                ("state", "=", "done"),
            ]
        )

        for pick in pickings:
            if pick.sale_id:
                for line in pick.move_lines:
                    attr = {
                        "product_id": line.sale_line_id.product_id.with_context(
                            {"lang": "it_IT", "tz": "Europe/Rome"}
                        ).display_name,
                        "categ": line.sale_line_id.product_id.categ_id.name,
                        "pid": line.sale_line_id.product_id.id,
                        "barcode": line.sale_line_id.product_id.barcode,
                        "qty": line.sale_line_id.product_uom_qty,
                        "total_price": line.sale_line_id.price_total,
                        "price_tax": line.sale_line_id.price_tax,
                        "picking_id": pick.name,
                        "date_done": pick.date_done,
                        "payment_method": pick.sale_order_payment_method.name,
                        "state": pick.state,
                        "picking_type_id": pick.picking_type_id.name,
                        "sale_id": pick.origin,
                        "tax_id": line.sale_line_id.tax_id.name,
                        "edizioni": 0,
                    }
                    if line.sale_line_id.product_id.product_brand_ept_id.id == edizioni_brand_id:
                        tax_value = tax_income_id.compute_all(attr["total_price"])
                        attr["edizioni"] += tax_value["total_included"] - tax_value["total_excluded"]
                    attr["edizioni"] = round(attr["edizioni"], 2)
                    attr["price_tax"] = round(attr["price_tax"], 2)
                    attr["total_price"] = round(attr["total_price"], 2)
                    results["done"].append(attr)

        refunds = self.search(
            [
                ("date_done", ">=", date_from),
                ("date_done", "<=", date_to),
                ("picking_type_id", "in", refund_picking_type_ids),
                ("state", "=", "done"),
            ]
        )
        for pick in refunds:
            for line in pick.move_lines:
                attr = {
                    "product_id": line.sale_line_id.product_id.with_context(
                        {"lang": "it_IT", "tz": "Europe/Rome"}
                    ).display_name,
                    "categ": line.sale_line_id.product_id.categ_id.name,
                    "pid": line.sale_line_id.product_id.id,
                    "barcode": line.sale_line_id.product_id.barcode,
                    "qty": line.sale_line_id.product_uom_qty,
                    "picking_id": pick.name,
                    "date_done": pick.date_done,
                    "payment_method": pick.sale_order_payment_method.name,
                    "state": pick.state,
                    "picking_type_id": pick.picking_type_id.name,
                    "sale_id": pick.origin,
                    "edizioni": 0,
                }
                order = self.env["sale.order"].search([("name", "=", pick.origin)])
                for pid in order.order_line:
                    if pid.product_id.id == line.product_id.id:
                        attr["total_price"] = pid.price_unit * line.sale_line_id.product_uom_qty
                        amount = pid.product_id.taxes_id.compute_all(attr["total_price"])
                        tax = amount["total_included"] - amount["total_excluded"]
                        attr["price_tax"] = tax
                        attr["tax_id"] = pid.tax_id.name
                        if pid.product_id.product_brand_ept_id.id == edizioni_brand_id:
                            tax_value = tax_income_id.compute_all(attr["total_price"])
                            attr["edizioni"] += tax_value["total_included"] - tax_value["total_excluded"]
                attr["edizioni"] = round(attr["edizioni"], 2)
                attr["price_tax"] = round(attr["price_tax"], 2)
                attr["total_price"] = round(attr["total_price"], 2)
                results["refund"].append(attr)

        return results


class ReceiptRegisterConfig(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_picking_type_ids = fields.Many2many(
        "stock.picking.type", "delivery_picking", string="Spedizioni ai clienti/vendite"
    )
    refund_picking_type_ids = fields.Many2many("stock.picking.type", "refund_picking", string="Resi")
    refund_delivery_cost = fields.Boolean(string="Contare le spese di spedizione nei resi")
    product_cod_id = fields.Many2one(
        "product.product", string="Prodotto contrassegno", config_parameter="receipt.register.product_cod_id"
    )
    tax_income_id = fields.Many2one(
        "account.tax", string="Imposta (debito)", config_parameter="receipt.register.tax_income_id"
    )
    edizioni_brand_id = fields.Many2one(
        "product.brand.ept", string="Brand di Edizioni", config_parameter="receipt.register.edizioni_brand_id"
    )

    @api.model
    def get_values(self):
        res = super(ReceiptRegisterConfig, self).get_values()
        icp = self.env["ir.config_parameter"].sudo()
        delivery_picking_type_ids = icp.get_param("receipt.register.delivery_picking_type_ids")
        refund_picking_type_ids = icp.get_param("receipt.register.refund_picking_type_ids")
        res.update(
            delivery_picking_type_ids=[(6, 0, literal_eval(delivery_picking_type_ids))]
            if delivery_picking_type_ids
            else False,
            refund_picking_type_ids=[(6, 0, literal_eval(refund_picking_type_ids))]
            if refund_picking_type_ids
            else False,
        )
        return res

    @api.model
    def set_values(self):
        res = super(ReceiptRegisterConfig, self).set_values()
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("receipt.register.delivery_picking_type_ids", self.delivery_picking_type_ids.ids)
        icp.set_param("receipt.register.refund_picking_type_ids", self.refund_picking_type_ids.ids)
        return res
