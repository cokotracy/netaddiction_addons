# Copyright 2019-2020 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2021-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
from openupgradelib import openupgrade  # pylint: disable=W7936

# We use the date of the main ecommerce migration as filter so the orders
# from the old version of the software will not be changed.
# Them will be changed manually.
ECOMMERCE_MIGRATION_DATE = '2021-10-03'


@openupgrade.migrate()
def migrate(env, version):
    logger = logging.getLogger(
        "odoo.addons.netaddiction_order.migrations.14.0.1.3.4"
    )
    # Get order for date and state
    orders = env['sale.order'].sudo().search([
        ('state', '=', 'problem'),
        ('date_order', '>', ECOMMERCE_MIGRATION_DATE),
        ])
    orders_nr = len(orders)
    logger.info("Hi Neo, thanks for choosing the red pill!")
    logger.info(f"The migration will involve {orders_nr} orders.")
    logger.info(f"Orders are: {orders.ids}.")
    if not orders:
        logger.info("Nothing to do here... Bye!")
        return
    logger.info(
        f"The orders have been filtered with the following criteria: "
        f"'Order date > {ECOMMERCE_MIGRATION_DATE}' and `state = problem`"
        )
    logger.info("Move orders state from `problem` to `cancel`")
    # Change state manually bwcause we haven't invoices and we don't need
    # to use cancel wizard
    orders.write({'state': 'cancel'})
    logger.info("Move orders state from `cancel` to `draft`")
    orders.action_draft()
    logger.info("Move orders state from `draft` to `sale`")
    orders.action_confirm()
    logger.info("Set `problem` flag in all the orders")
    orders.write({'problem': True})
    logger.info("Done. See you the next time :)")
