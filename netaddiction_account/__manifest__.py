# Copyright 2019 Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Netaddiction Account',
    'version': '14.0.1.0.0',
    'category': 'Account',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_it_fiscalcode',
    ],
    'data': [
        'views/res_partner.xml',
        # 'views/account_views.xml',
        'security/ir.model.access.csv',
        'wizard/check_csv_cod.xml',
    ],
}
