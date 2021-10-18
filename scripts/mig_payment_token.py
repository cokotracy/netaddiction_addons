import erppeek
import ssl
import json
import stripe

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


_error_logs = []

odoo9 = erppeek.Client(URL9, DB9, LOGIN9, PASSWORD9)
odoo14 = erppeek.Client(URL14, DB14, LOGIN14, PASSWORD14)

cc_model_9 = odoo9.model("netaddiction.partner.ccdata")
pt_model_14 = odoo14.model("payment.token")
aq_model_14 = odoo14.model("payment.acquirer")

_cache_customer = []


def get_stripe_customer(partner):
    if _cache_customer:
        f = next(item for item in _cache_customer if item["partner"] == partner.id)
        if f:
            return f.get("customer")
    customer = stripe.Customer.list(email=partner.email)
    try:
        customer_id = customer.data[0]["id"]
    except IndexError:
        return

    _cache_customer.append({"partner": partner.id, "customer": customer_id})
    return customer_id


def main():
    try:
        acquirer = aq_model_14.browse([("provider", "=", "netaddiction_stripe"), ("state", "=", "enabled")])[0]
    except IndexError:
        return
    stripe.api_key = acquirer.netaddiction_stripe_sk

    for cc in tqdm(cc_model_9.browse([("token", "ilike", "card")], limit=None)):
        user_pt = pt_model_14.search(
            [
                ("netaddiction_stripe_payment_method", "=", cc.token),
                ("partner_id", "=", cc.customer_id.id),
            ]
        )
        if not user_pt:
            customer = get_stripe_customer(cc.customer_id)
            if not customer:
                continue
            try:
                token = pt_model_14.create(
                    {
                        "acquirer_id": acquirer.id,
                        "partner_id": cc.customer_id.id,
                        "netaddiction_stripe_payment_method": cc.token,
                        "name": cc.last_four,
                        "brand": cc.ctype,
                        "acquirer_ref": customer,
                        "default_payment": cc.default,
                    }
                )
                print(f"Token migrato: {token}")
            except Exception as e:
                _error_logs.append({"token non migrato": cc.token})

    if _error_logs:
        with open("~/error_cc_migration.json", "w") as fp:
            json.dump(_error_logs, fp, sort_keys=True, indent=4, separators=(",", ": "))


if __name__ == "__main__":
    main()
