import erppeek
import ssl

from datetime import date
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

products_9 = odoo9.model("product.product")
products_14 = odoo14.model("product.product")


def main():
    for product_9 in tqdm(products_9.browse([("out_date", ">", date.today().strftime("%d-%m-%Y"))])):
        products_14.browse([("id", "=", product_9.id)]).write(
            {"inventory_availability": "never" if product_9.sale_ok else "always"}
        )


if __name__ == "__main__":
    main()
