# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

def migrate(cr, version):
    if not version:
        return
    # Change value of `base` field on pricelist items
    # because we will delete `final_price` value
    cr.execute(
        'UPDATE product_pricelist_item '
        'SET base = \'list_price\' '
        'WHERE base = \'final_price\''
        )
    # Empty `pricelist.condition` table
    # (and m2m relations with pricelist in cascade)
    cr.execute('TRUNCATE TABLE pricelist_condition CASCADE')
