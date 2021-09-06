#! /usr/bin/env python3

# Copyright 2021 Rapsodoo Italia SrL (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# It looks like list_price is not properly set after the 9->14 migration of
# NetAddiction. This script retrieves the data from the existing Odoo 9
# instance and restores the prices on Odoo 14


import erppeek
import ssl

# The Odoo 9 has an invalid certificate sometimes. We are confident enough
# in it to skip the certificate validation
ssl._create_default_https_context = ssl._create_unverified_context

URL14 = 'http://localhost:8069'
DB14 = 'netaddiction'
LOGIN14 = 'ecommerce-servizio@netaddiction.it'
PASSWORD14 = '2VBrhX^49Qh!'

URL9 = 'https://backoffice-staging.netaddiction.it'
DB9 = 'odoo'
LOGIN9 = 'ecommerce-servizio@netaddiction.it'
PASSWORD9 = '2VBrhX^49Qh!'


def main():
    odoo9 = erppeek.Client(URL9, DB9, LOGIN9, PASSWORD9)
    odoo14 = erppeek.Client(URL14, DB14, LOGIN14, PASSWORD14)

    print("Reading data on Odoo 9. This may take a while...")
    data9 = odoo9.read(
        'product.product',
        [('active', '=', True)],
        ('id', 'list_price', 'out_date')
    )

    product14 = odoo14.model('product.product')
    for item9 in data9:
        print(f"Processing product ID {item9['id']}")
        try:
            product14.browse(item9['id']).fix_price = item9['list_price']
        except Exception:
            print(f"ERROR: Can't assign fix_price to product ID {item9['id']}")
        try:
            product14.browse(item9['id']).out_date = item9['out_date']
        except Exception:
            print(f"ERROR: Can't assign out_date to product ID {item9['id']}")


if __name__ == '__main__':
    main()
