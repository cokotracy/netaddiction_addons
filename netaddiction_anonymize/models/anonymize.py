# -*- coding: utf-8 -*-

from openerp import models, api

class Anonymizer(models.Model):
    _name = "netaddiction_anonymizer"

    @api.model
    def anonymize(self, user_ids):
        """
        anonimizza tutti gli utenti i cui id sono nella lista user_ids
        in user_ids passare gli id padri
        """
        users = self.env['res.partner'].search([('id', 'in', user_ids)])
        users.anonymize_myself()

class User(models.Model):
    _inherit = "res.partner"

    @api.multi
    def anonymize_myself(self):
        for user in self:
            parent_name_anonymize = 'User_%s' % user.id
            phone = '00000000'
            mobile = '00000000'
            email = '%s_email' % parent_name_anonymize

            user.with_context({'skip_reduplicate_partner': True}).write({
                'name': parent_name_anonymize,
                'vat': '',
                'fiscalcode': '',
                'phone': phone,
                'mobile': mobile,
                'email': email
            })

            for child in user.child_ids:
                child_name_anonymize = 'Child_%s_of_%s' % (child.id, user.id)
                email = '%s_email' % child_name_anonymize
                xxxxx = 'XXXXX'
                child.with_context({'skip_reduplicate_partner': True}).write({
                    'name': child_name_anonymize,
                    'phone': phone,
                    'mobile': mobile,
                    'email': email,
                    'company_address': xxxxx,
                    'street': xxxxx,
                    'street2': '0',
                    'city': xxxxx,
                    'state_id': False,
                    'zip': '00000',
                    'country_id': False,
                    'vat': '',
                    'fiscalcode': '',
                })

            deactivate = self.search([('parent_id', '=', user.id), ('active', '=', False)])

            for child in deactivate:
                child_name_anonymize = 'Child_%s_of_%s' % (child.id, user.id)
                email = '%s_email' % child_name_anonymize
                xxxxx = 'XXXXX'
                child.with_context({'skip_reduplicate_partner': True}).write({
                    'name': child_name_anonymize,
                    'phone': phone,
                    'mobile': mobile,
                    'email': email,
                    'company_address': xxxxx,
                    'street': xxxxx,
                    'street2': '0',
                    'city': xxxxx,
                    'state_id': False,
                    'zip': '00000',
                    'country_id': False,
                    'vat': '',
                    'fiscalcode': '',
                })
