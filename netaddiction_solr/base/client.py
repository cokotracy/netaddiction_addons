import pysolr


class Solr(object):
    URL = 'http://localhost:8983/solr/odoo'
    TIMEOUT = 5

    @classmethod
    def get(cls):
        return pysolr.Solr(cls.URL, timeout=cls.TIMEOUT)
