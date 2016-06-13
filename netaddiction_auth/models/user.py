# -*- coding: utf-8 -*-

from hashlib import md5

from openerp import models
from openerp.exceptions import AccessDenied


class User(models.Model):
    _inherit = 'res.users'

    def check_credentials(self, cr, uid, password):
        try:
            return super(User, self).check_credentials(cr, uid, password)
        except ValueError:
            cr.execute('SELECT password_crypt FROM res_users WHERE id = %s AND active', (uid, ))

            if cr.rowcount:
                encrypted = cr.fetchone()[0]

                # MD5 without SALT
                if len(encrypted) == 32:
                    if encrypted == md5(password).hexdigest():
                        self.upgrade_password(cr, uid, password)
                        return super(User, self).check_credentials(cr, uid, password)

                # MD5 with SALT
                elif len(encrypted) == 35 and ':' in encrypted:
                    encrypted, salt = encrypted.split(':')
                    if encrypted == md5(salt + password).hexdigest():
                        self.upgrade_password(cr, uid, password)
                        return super(User, self).check_credentials(cr, uid, password)

            raise AccessDenied()

    def upgrade_password(self, cr, uid, password):
        self._set_password(cr, uid, uid, password)
        self.invalidate_cache(cr, uid)
