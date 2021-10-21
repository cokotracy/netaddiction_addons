# Copyright 2021 Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _fix_tax_included_price_company(self, price, prod_taxes, line_taxes, company_id):
        # If the fiscal position of the partner is B2B, odoo substitutes the VAT from
        # INC to not-INC, and recalculates the price_unit. This is not a desired
        # behaviour for us. So, in these cases, we just skip it all and give back
        # the original price
        if self._context.get('is_cart_update'):
            website_id = self._context.get('website_id')
            if website_id and self.env['website'].browse(website_id).isB2B:
                return price
        return super()._fix_tax_included_price_company(price, prod_taxes, line_taxes, company_id)
