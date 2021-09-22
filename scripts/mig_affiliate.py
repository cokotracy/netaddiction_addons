import erppeek
import random
import ssl
import json

from tqdm import tqdm

ssl._create_default_https_context = ssl._create_unverified_context

URL14 = "http://127.0.0.1:8069"
DB14 = "odoo_multiplayer_com"
LOGIN14 = "ecommerce-servizio@netaddiction.it"
PASSWORD14 = "2VBrhX^49Qh!"

URL9 = "https://backoffice-staging.netaddiction.it"
DB9 = "odoo"
LOGIN9 = "ecommerce-servizio@netaddiction.it"
PASSWORD9 = "2VBrhX^49Qh!"

EXCLUDE_PRODUCT = [x for x in range(1, 10)]

_error_logs = []

odoo9 = erppeek.Client(URL9, DB9, LOGIN9, PASSWORD9)
odoo14 = erppeek.Client(URL14, DB14, LOGIN14, PASSWORD14)

partner_model_14 = odoo14.model("res.partner")
affiliate_model_9 = odoo9.model("netaddiction.partner.affiliate")


def set_as_affiliate(user_id):
    partner = partner_model_14.browse(user_id)
    partner.is_affiliate = True
    partner.res_affiliate_key = "".join(
        random.choice("0123456789ABCDEFGHIJ0123456789KLMNOPQRSTUVWXYZ") for i in range(8)
    )


def set_affiliate_orders(affiliate_id, partner_id):
    order_history = odoo9.read(
        "netaddiction.partner.affiliate.order.history",
        [("affiliate_id", "=", affiliate_id), ("order_state", "=", "sale")],
    )
    print(f"Migrate orders for affiliate: {affiliate_id}")
    for order in tqdm(order_history):
        order_lines = get_order_lines(order["order_id"])
        if not order_lines:
            continue
        for line in order_lines:
            if line["product_tmpl_id"][0] in EXCLUDE_PRODUCT:
                continue
            if odoo14.read("affiliate.visit", [("sales_order_line_id", "=", line["id"])]):
                continue
            product_tmpl_id = line["product_tmpl_id"][0]
            try:
                odoo14.create(
                    "affiliate.visit",
                    {
                        "affiliate_method": "pps",
                        "affiliate_key": "9JWDV3C2",
                        "affiliate_partner_id": partner_id,
                        "url": "",
                        "ip_address": "",
                        "type_id": product_tmpl_id,
                        "affiliate_type": "product",
                        "type_name": line["product_id"][0],
                        "sales_order_line_id": line["id"],
                        "convert_date": line["create_date"],
                        "affiliate_program_id": 1,
                        "product_quantity": line["product_uom_qty"],
                        "is_converted": True,
                        "commission_type": "d",
                    },
                )
            except Exception as e:
                _error_logs.append({"order line": line["id"]})


def get_order_lines(order_id):
    _order_lines_list = []
    try:
        order_lines = odoo9.read("sale.order", [("id", "=", order_id[0])], ("order_line"))[0]
    except Exception:
        return
    else:
        for line_id in order_lines:
            line = odoo9.read("sale.order.line", [("id", "=", line_id)])
            if line:
                _order_lines_list.append(line[0])
    return _order_lines_list


def main():
    for affiliate in affiliate_model_9.browse([], limit=None):
        if not partner_model_14.browse([("is_affiliate", "=", True), ("id", "=", affiliate.partner_id.id)]):
            set_as_affiliate(affiliate.partner_id.id)
        set_affiliate_orders(affiliate.id, affiliate.partner_id.id)

    if _error_logs:
        with open("error_affiliate_migration.json", "w") as fp:
            json.dump(_error_logs, fp, sort_keys=True, indent=4, separators=(",", ": "))


if __name__ == "__main__":
    main()
