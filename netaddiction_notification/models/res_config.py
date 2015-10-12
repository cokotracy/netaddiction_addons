# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Configuration(models.TransientModel):
    _name = 'netaddiction.notification.settings'
    _inherit = 'res.config.settings'

    default_active = fields.Boolean(
        string="Attivo",
        help="""Se disattivo il software non
            loggerà alcuna modifica""",
        default_model="netaddiction.notification.settings")

    #product log
    default_product_product = fields.Boolean(
        string="Prodotti",
        default_model="netaddiction.notification.settings"
    )

    
