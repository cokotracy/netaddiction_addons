from openerp import api, models

from ..base.client import Solr


class Cron(models.Model):
    _name = 'netaddiction_solr.optimize'

    @api.model
    def run(self):
        solr = Solr.get()
        solr.optimize()
