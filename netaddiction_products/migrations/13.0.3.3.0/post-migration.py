# Copyright 2021-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def create_public_category(env, name, parent_id=False):
    return env['product.public.category'].create({
        'name': name,
        'parent_id': parent_id,
    })


def migrate(cr, version):
    """
    Create a new product.public.category matching each and every
    product.category.
    Also, assign all products of the product.category to the newly created
    product.public.category
    """
    if not version:
        return
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        product_category_obj = env['product.category']
        product_template_obj = env['product.template']

        root_categ = product_category_obj.search(
            [('parent_id', '=', False)],
            limit=1,
        )
        parent_public_categ = create_public_category(env, root_categ.name)

        for categ in product_category_obj.search([('parent_id', '!=', False)]):
            public_categ = create_public_category(
                env, categ.name, parent_id=parent_public_categ.id
            )
            product_template_obj.search(
                [('categ_id', '=', categ.id)]
            ).write({
                'public_categ_ids': [(4, public_categ.id)]
            })
