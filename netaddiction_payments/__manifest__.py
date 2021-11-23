# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


{
    "name": "NetAddiction Payments",
    "summary": "Nuova Gestione Pagamenti",
    "description": """
    Modulo della gestione degi pagamenti
    """,
    "author": "Netaddiction",
    "website": "http://www.netaddiction.it",
    "category": "Technical Settings",
    "version": "14.0.2.7.1",
    "depends": [
        "account",
        "product",
        "sale",
    ],
    "data": [
        "data/account_journal.xml",
        "data/cash_on_delivery.xml",
        "views/sale_order.xml",
        "views/stock_picking.xml",
        "views/stripe/templates.xml",
        "views/stripe/payment_views.xml",
        "wizard/stripe_payment_transaction.xml",
        "security/ir.model.access.csv",
    ],
}
