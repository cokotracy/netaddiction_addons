#! /usr/bin/env python3

# Copyright 2021 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# It looks like list_price is not properly set after the 9->13 migration of
# NetAddiction. This script retrieves the data from the existing Odoo 9
# instance and restores the prices on Odoo 13


import erppeek

URL13 = 'http://localhost:2069'
DB13 = 'netaddiction_migrazione'
LOGIN13 = 'ecommerce-servizio@netaddiction.it'
PASSWORD13 = 'b*Y^x#AR2D71'

URL9 = 'https://backoffice-staging.netaddiction.it'
DB9 = 'odoo'
LOGIN9 = 'ecommerce-servizio@netaddiction.it'
PASSWORD9 = 'b*Y^x#AR2D71'


def main():
    odoo9 = erppeek.Client(URL9, DB9, LOGIN9, PASSWORD9)
    odoo13 = erppeek.Client(URL13, DB13, LOGIN13, PASSWORD13)

    print("Reading data on Odoo 9. This may take a while...")
    data9 = odoo9.read(
        'product.product',
        [('active', '=', True)],
        ('id', 'list_price')
    )

    product13 = odoo13.model('product.product')
    for item9 in data9:
        print(f"Processing product ID {item9['id']}")
        try:
            product13.browse(item9['id']).list_price = item9['list_price']
        except Exception:
            print(f"ERROR: Skipping product ID {item9['id']}")


if __name__ == '__main__':
    main()
