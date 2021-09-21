from datetime import datetime
import erppeek
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

URL14 = "http://127.0.0.1:8069"
DB14 = "odoo_multiplayer_com"
LOGIN14 = "ecommerce-servizio@netaddiction.it"
PASSWORD14 = "2VBrhX^49Qh!"

URL9 = "https://backoffice.netaddiction.it"
DB9 = "odoo"
LOGIN9 = "ecommerce-servizio@netaddiction.it"
PASSWORD9 = "b*Y^x#AR2D71"

EXCLUDE_PRODUCT = [x for x in range(1, 10)]

odoo9 = erppeek.Client(URL9, DB9, LOGIN9, PASSWORD9)
odoo14 = erppeek.Client(URL14, DB14, LOGIN14, PASSWORD14)


def set_affiliate(user_id):
    pass


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
    partner_ids = odoo9.read("netaddiction.partner.affiliate", [], ("partner_id"))
    print(partner_ids)
    # set_affiliate(user_id)

    # order_history = odoo9.read(
    #     "netaddiction.partner.affiliate.order.history", [("affiliate_id", "=", 51), ("order_state", "=", "sale")]
    # )
    # for order in order_history:
    #     order_lines = get_order_lines(order["order_id"])
    #     if not order_lines:
    #         continue
    #     for line in order_lines:
    #         if line["product_tmpl_id"][0] in EXCLUDE_PRODUCT:
    #             continue
    #         if odoo14.read("affiliate.visit", [("sales_order_line_id", "=", line["id"])]):
    #             continue
    #         product_tmpl_id = line["product_tmpl_id"][0]
    #         odoo14.create(
    #             "affiliate.visit",
    #             {
    #                 "affiliate_method": "pps",
    #                 "affiliate_key": "9JWDV3C2",
    #                 "affiliate_partner_id": 742846,
    #                 "url": "",
    #                 "ip_address": "",
    #                 "type_id": product_tmpl_id,
    #                 "affiliate_type": "product",
    #                 "type_name": line["product_id"][0],
    #                 "sales_order_line_id": line["id"],
    #                 "convert_date": line["create_date"],
    #                 "affiliate_program_id": 1,
    #                 "product_quantity": line["product_uom_qty"],
    #                 "is_converted": True,
    #                 "commission_type": "d",
    #             },
    #         )


if __name__ == "__main__":
    main()
