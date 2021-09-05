# -*- coding: utf-8 -*-
#################################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
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
# If not, see <https://store.webkul.com/license.html/>;
#################################################################################
{
    "name"                 : "wk_affiliate_coupon",
    "summary"              :  """The module allows you to create discount coupons for Affiliate Management module""",
    "category"             :  "Website",
    "version"              :  "14.0.1.0.0",
    "sequence"             :  1,
    "author"               :  "Webkul Software Pvt. Ltd.",
    "license"              :  "Other proprietary",
    "description"          :  """The module allows you to create discount coupons  for Affiliate Management module""",

    # any module necessary for this one to work correctly
    "depends"              : ['affiliate_management', 'coupon', 'sale_coupon'],

    # always loaded
    'data'                  : [
                                'security/ir.model.access.csv',
                                'data/coupon_data_view.xml',
                                'data/demo.xml',
                                'views/inherit_affiliate_program_view.xml',
                                'views/coupons_program_view.xml',
                                # 'views/inherit_affiliate_res_config.xml',
                                'views/inherit_affiliate_visit.xml',
                                'views/coupon_program.xml',
                                'views/templates.xml',
                                # 'views/inherit_affilate_report.xml'
                               ],
}
