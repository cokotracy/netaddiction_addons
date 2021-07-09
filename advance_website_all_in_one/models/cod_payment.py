# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare


class CODAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cod', 'Cash on Delivery')], ondelete={'cod': 'set default'})

    def _get_providers(self):
        providers = super(CODAcquirer, self)._get_providers()
        providers.append(['cod', _('Cash on Delivery')])
        return providers

    def cod_get_form_action_url(self):
        return '/cod/payment/feedback'

    def cod_compute_fees(self, amount, currency_id, country_id):
        """ Compute paypal fees.

            :param float amount: the amount to pay
            :param integer country_id: an ID of a res.country, or None. This is
                                       the customer's country, to be compared to
                                       the acquirer company country.
            :return float fees: computed fees
        """
        if not self.fees_active:
            return 0.0
        country = self.env['res.country'].browse(country_id)
        if country and self.company_id.country_id.id == country.id:
            fixed = self.delivery_fees
        else:
            fixed = self.delivery_fees
        fees = fixed #(percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
        return fees

class CODPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _cod_form_get_tx_from_data(self, data):
        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        tx = self.search([('reference', '=', reference)])
        tx.update({
            'state':'pending'
            })

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: