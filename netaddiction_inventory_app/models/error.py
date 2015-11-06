# -*- coding: utf-8 -*-
class Error(object):
    _msg = ''

    def __init__(self):
        pass

    def get_error_msg(self):
        return self._msg

    def set_error_msg(self,err):
        self._msg = str(err)
