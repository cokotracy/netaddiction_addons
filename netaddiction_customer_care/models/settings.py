# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

ERROR_COMPANY = u"Azienda già inserita"
ERROR_EMAIL = u"E-mail già inserita"

class CompanyMail(models.Model):
    _name = 'netaddiction.project.issue.settings.companymail'

    company_id = fields.Many2one(comodel_name="res.company",string="Azienda",ondelete="restrict",required="True")
    email = fields.Char("E-mail",required="True")

    @api.one
    @api.constrains('company_id','email')
    def _check_one_of(self):
        to_search = [('company_id','=',self.company_id.id)]
        get = self.search(to_search)
        if len(get)>1:
            raise ValidationError(ERROR_COMPANY)

        to_search = [('email','=',self.email)]
        get = self.search(to_search)
        if len(get)>1:
            raise ValidationError(ERROR_EMAIL)
    