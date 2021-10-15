{
    'name': "Netaddiction Warehouse",
    'summary': "Magazzino Netaddiction",
    'author': "NetAddiction",
    'website': "http://www.netaddiction.it",
    'category': 'Warehouse Management',
    'version': '14.0.1.8.1',
    'depends': [
        'base',
        'advance_website_all_in_one',
        'delivery',
        # 'mrp',
        # 'netaddiction_customer',          TODO: will it be migrated?
        'netaddiction_orders',
        'netaddiction_payments',
        'netaddiction_products',
        # 'netaddiction_special_offers',    NB: won't be migrated
        'partner_manual_rank',
        'product',
        'purchase',
        'sale',
        'sale_stock',
        'stock',
        'stock_barcode',
        'stock_picking_batch',
        'web',
        'web_onchange_enterkey',
        'delay_payment',
        'delay_payment_stock_picking_batch',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_carriers.xml',
        'data/ir_cron.xml',
        'data/mail_message_subtype.xml',
        'data/stock_location.xml',
        'reports/report.xml',
        'reports/template/bolla_di_spedizione.xml',
        'reports/template/stock.xml',
        'templates/allocation.xml',
        'templates/assets.xml',
        'templates/inventory_app.xml',
        'templates/pick_up.xml',
        'templates/search.xml',
        'templates/top_menu.xml',
        'views/actions_client.xml',
        'views/actions_url.xml',
        'views/assets.xml',
        'views/delivery_carrier.xml',
        'views/netaddiction_inventory_reports.xml',
        'views/netaddiction_manifest.xml',
        'views/netaddiction_products_movement.xml',
        'views/netaddiction_warehouse_operations_settings.xml',
        'views/netaddiction_wh_locations.xml',
        'views/netaddiction_wh_locations_line.xml',
        'views/product_product.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        #'views/stock_inventory.xml',
        'views/stock_move.xml',
        'views/stock_picking.xml',
        'views/stock_picking_batch.xml',

        # Leave menus for last to upload every action and view beforehand
        'views/menus.xml',
    ],
    'qweb': [
        'static/src/xml/allocation.xml',
        'static/src/xml/carico.xml',
        'static/src/xml/content_reso.xml',
        # TODO the action client reso fornitore has been removed
        # 'static/src/xml/content_supplier_reverse.xml',
        'static/src/xml/controllo_pick_up.xml',
        'static/src/xml/inventory_reports.xml',
        'static/src/xml/pickup.xml',
        'static/src/xml/search.xml',
        'static/src/xml/spara_pacchi.xml',
        'static/src/xml/warehouse.xml',
    ],
    'application': True,
    'installable': True,
}
