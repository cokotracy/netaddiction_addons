# -*- coding: utf-8 -*-

from openerp import models, fields, api
from collections import defaultdict
from datetime import datetime,date,timedelta

class Wave(models.Model):
    _inherit = "stock.picking.wave"

    file_ddt = fields.Binary(string="Scansione Documento di Trasporto")