import pysolr


class Solr(object):
    URL = 'http://localhost:8983/solr/odoo'  # TODO personalizzabile
    TIMEOUT = 10

    @classmethod
    def get(cls):
        return pysolr.Solr(cls.URL, timeout=cls.TIMEOUT)
