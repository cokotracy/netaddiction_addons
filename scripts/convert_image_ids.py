# This script should be executed inside a NetAddiction Odoo 14 shell. It will
# create records of product.image for each product with available image_ids
# records.
#
# If you are wondering why there is such a weird setup of try/except blocks,
# let's have a beer together and talk about how shameful images and attachments
# management is on Odoo.
#
# This script is idempotent and thought to be re-run multiple times preventing
# the creation of duplicate images.

products = self.env['product.product'].search([('image_ids', '!=', False), ('product_variant_image_ids', '=', False)])

for count, product in enumerate(products):
    try:
        for attachment in product.image_ids:
            self.env['product.image'].create({'name': product.name, 'image_1920': attachment.datas, 'product_tmpl_id': product.product_tmpl_id.id, 'product_variant_id': product.id})
    except:
        # This rollback is needed to avoid creating duplicated images at later runs
        self._cr.rollback()
        print(f"Can't process images for product ID {product.id}")
        continue

    try: 
        self._cr.commit()
    except:
        # This rollback is needed to avoid creating duplicated images at later runs
        self._cr.rollback()
        print(f"Can't commit images for product ID {product.id}")
        continue

    print(f"Product ID {product.id} processed. {len(products)-count} products to go")

