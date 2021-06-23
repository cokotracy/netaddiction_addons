# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Odoo Affiliate Management",
  "summary"              :  """Affiliate extension for odoo E-commerce store""",
  "category"             :  "Website",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Saurabh Gupta",
  "website"              :  "https://store.webkul.com/Odoo-Affiliate-Management.html",
  "description"          :  """Odoo Affiliate Extension for Affiliate Management""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=affiliate_management&lifetime=90&lout=1&custom_url=/",
  "depends"              :  [
                             'sales_team',
                             'website_sale',
                             'wk_wizard_messages',
                             'web',
                             'web_tour',
                             'auth_signup',
                             'account',
                            ],
  "data"                 :  [
                             'security/affiliate_security.xml',
                             'security/ir.model.access.csv',
                             'views/affiliate_pragram_form_view.xml',
                             'data/automated_scheduler_action.xml',
                             'views/affiliate_manager_view.xml',
                             'data/sequence_view.xml',
                             'views/affiliate_visit_view.xml',
                             'views/affiliate_config_setting_view.xml',
                             'views/res_users_inherit_view.xml',
                             'views/account_invoice_inherit.xml',
                             'views/affiliate_tool_view.xml',
                             'views/affiliate_image_view.xml',
                             'views/advance_commision_view.xml',
                             'views/affiliate_pricelist_view.xml',
                             'views/affiliate_banner_view.xml',
                             'views/report_template.xml',
                             'views/payment_template.xml',
                             'views/index_template.xml',
                             'views/tool_template.xml',
                             'views/header_template.xml',
                             'views/footer_template.xml',
                             'views/join_email_template.xml',
                             'views/signup_template.xml',
                             'views/affiliate_request_view.xml',
                             'views/welcome_mail_tepmlate.xml',
                             'views/reject_mail_template.xml',
                             'views/tool_product_link_template.xml',
                             'views/about_template.xml',
                             'data/default_affiliate_program_data.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  99,
  "currency"             :  "USD",
}