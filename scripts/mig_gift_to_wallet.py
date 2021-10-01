import erppeek
import ssl

from tqdm import tqdm

ssl._create_default_https_context = ssl._create_unverified_context

URL14 = "http://127.0.0.1:8069"
DB14 = "netaddiction"
LOGIN14 = "ecommerce-servizio@netaddiction.it"
PASSWORD14 = "2VBrhX^49Qh!"

URL9 = "https://backoffice-staging.netaddiction.it"
DB9 = "odoo"
LOGIN9 = "ecommerce-servizio@netaddiction.it"
PASSWORD9 = "2VBrhX^49Qh!"

odoo9 = erppeek.Client(URL9, DB9, LOGIN9, PASSWORD9)
odoo14 = erppeek.Client(URL14, DB14, LOGIN14, PASSWORD14)


def set_money_wallet(partner_id, money):
    partner = odoo14.model("res.partner").browse(partner_id)
    partner.wallet_balance = money


def main():
    for partner in tqdm(odoo9.model("res.partner").browse([("gift_ids", "!=", [])])):
        if partner.gift_ids:
            total_gift = 0.0
            for gift in partner.gift_ids:
                total_gift += gift.value
            set_money_wallet(partner.id, total_gift)


if __name__ == "__main__":
    main()
