# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class PartnerGDPRDisable(models.TransientModel):

    _name = 'partner.gdpr.disable'
    _description = "Partner GDPR - Disable"

    @api.model
    def _default_partner_id(self):
        return self.env.context.get('active_id', False)

    documents = fields.Integer(
        default=-1,
    )

    document_ids = fields.One2many(
        'partner.gdpr.disable.line',
        'wizard_id',
        string='Documents',
        readonly=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        default=_default_partner_id,
        )

    def _reopen_wizard(self):
        action = self.env.ref(
            'partner_gdpr.action_partner_gdpr_disable').read()[0]
        action['res_id'] = self.id
        action['res_ids'] = [self.id, ]
        return action

    def _get_documents_sale_order(self, count=None):
        domain = [('partner_id', '=', self.partner_id.id),
                  ('state', 'in', ('draft', 'sent')), ]
        sale_model = self.env['sale.order'].sudo()
        if count:
            return sale_model.search_count(domain)
        else:
            return sale_model.search(domain)

    # To extend managed model, inherit this function to append
    # specific model records.
    # Create a function called
    #
    # `def _get_document_YOUR_MODEL(self, count=None):`
    #
    # to return valid records so `partner.gdpr.disable.line`
    # can automatically open them on button click and show them to user.
    def _get_documents(self):
        self.ensure_one()
        documents = []
        sales = self._get_documents_sale_order(count=True)
        if sales:
            action_id = self.env.ref(
                'partner_gdpr.gdpr_partner_open_sale_action').id
            documents.append((0, 0, {
                'action_id': action_id,
                'model': 'sale.order',
                'name': _('Sale Documents'),
                'quantity': sales,
                }))
        return documents

    def check_documents(self):
        self.ensure_one()
        self.document_ids = self._get_documents()
        self.documents = sum(self.document_ids.mapped('quantity'))
        return self._reopen_wizard()

    def disable_partner(self):
        self.ensure_one()
        self.partner_id.active = False
        return True


class PartnerGDPRDisableLine(models.TransientModel):

    _name = 'partner.gdpr.disable.line'
    _description = "Partner GDPR - Disable - Line"

    action_id = fields.Many2one(
        'ir.actions.act_window',
        string='action',
        )

    model = fields.Char(required=True)

    name = fields.Char(required=True)

    quantity = fields.Integer()

    wizard_id = fields.Many2one(
        'partner.gdpr.disable',
        string='Wizard',
    )

    def manage_documents(self):
        self.ensure_one()
        get_documents = getattr(
            self.wizard_id, f'_get_documents_{self.model}'.replace('.', '_'))
        records = get_documents()
        action = self.action_id.read()[0]
        action['domain'] = [('id', 'in', records.ids)]
        return action
