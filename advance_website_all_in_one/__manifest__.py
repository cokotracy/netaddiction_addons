# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Advance Website eCommerce All in One Bundle - Odoo",
    "version" : "14.0.1.1.0",
    "category" : "Website",
    "depends" : ['website_all_in_one'],
    "author": "BrowseInfo",
    "summary": 'Website all in one e-Commerce all in one website Stock website Discount website Label website review website all features website wallet website loyalty website cash on delivery COD all website feature all eCommerce all features website seo url redirect',
    "description": """
        This apps helps for website cart advance setting,
        website loyalty rewards and redeem management, 
        to add cash on delivery as payment method on odoo eCommerce, 
        create gift and discount voucher which is going to use for Website,
        visible/hide the product on shop based on partner/Customer,
        SEO-URL Redirect/Rewrite on Odoo website,
        Show Product Variant Description on Website
    """ , 
    "website" : "https://www.browseinfo.in",
    "price": 100,
    "currency": 'EUR',
    "data": [
        'views/advance_cart_view.xml',
        'views/advance_cart_template.xml',
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/web_loyalty.xml',
        'views/cod_view.xml',
        'views/cod_template.xml',
        'views/cod_collection_report.xml',
        'views/report_cod_collection.xml',
        'data/payment_acquirer_data.xml',
        'views/web_gift_coupon.xml',
        'views/report_web_gift_coupon.xml',
        'views/voucher_template.xml',
        'views/views.xml',
        'views/res_partner_view.xml',
        'wizard/seourl_update_views.xml',
        'views/product_url_redirect_view.xml',
        'views/seo_template.xml',
        'views/product_variant_template.xml',
    ],
    'qweb': [
        'static/src/xml/Website.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url" : 'https://youtu.be/JABkKZW6VSY',
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
