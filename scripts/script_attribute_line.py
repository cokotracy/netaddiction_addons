#! /usr/bin/env python

"""
This script is meant to rebuild the missing product.attribute.line on
the Odoo 9 Netaddiction database.

To run this script:
0- ssh to the APP01-STAGING server
1- cd to /home/application
2- start the odoo virtualenv:
    source .virtualenvs/odoo/bin/activate
3- launch the script via the odoo shell:
    echo "exec(open('/home/application/script_attribute_line.py').read())" | /opt/odoo/core/openerp-server shell -c /opt/odoo/odoo.conf --xmlrpc-port=9999 -d odoo
"""

product_attribute_line_obj = self.env['product.attribute.line']

for template in self.env['product.product'].search([]).mapped('product_tmpl_id'):
    print "Processing product.template ID: " + str(template.id)

    products = template.product_variant_ids
    values = products.mapped('attribute_value_ids')
    attributes = values.mapped('attribute_id')

    for attribute in attributes:
        attr_values = values.filtered(lambda v: v.attribute_id.id == attribute.id)
        product_attribute_line_obj.create({
            'attribute_id': attribute.id,
            'product_tmpl_id': template.id,
            'value_ids': [(4, i) for i in attr_values.ids],
        })

self._cr.commit()
