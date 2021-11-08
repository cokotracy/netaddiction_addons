from odoo import models, fields

class CategoryDescriptionInherit(models.Model):
    _inherit = "product.public.category"
    description = fields.Text(name="description")
    primary_category = fields.Boolean('È la categoria principale?',default=False)