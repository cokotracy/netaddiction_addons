from odoo import fields, models

# TODO These two classes are only needed to garantee a smooth migration to 14.
# Once the db has been ported to 14 in prod, this whole file can be removed


class GiftType(models.Model):
    _name = 'netaddiction.gift.type'
    _description = 'netaddiction.gift.type'

class Gift(models.Model):
    _name = 'netaddiction.gift'
    _description = 'netaddiction.gift'


