class NAWHError(Exception):
    """ Netaddiction Warehouse custom error """

    def __init__(self, msg=None):
        self.msg = msg or ''
