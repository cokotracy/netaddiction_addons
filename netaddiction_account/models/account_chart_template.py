# Copyright 2021 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.model
    def existing_accounting(self, company_id):
        """ This method is only invoked by res.config.settings. Unfortunately,
        it takes ages to complete, and we know for sure that on NetAddiction
        it should always return True. Therefore, we are skipping the whole
        elaboration and returning the proper value"""

        return True
