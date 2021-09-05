# Copyright 2018-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.add_fields(env, [('city_id', 'res.better.zip', 'res_better_zip', 'many2one', 'integer', 'base_location',)])
    
    openupgrade.rename_columns(
        env.cr, {
            'res_partner': [
                ('zip_id', None),
            ]
        }
    )
    openupgrade.remove_tables_fks(env.cr, ['res_better_zip'])
