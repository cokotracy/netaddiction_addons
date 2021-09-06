# This script should be executed inside a NetAddiction Odoo 9 shell. It will
# set the product template price to the min price of each variant of its


products = self.env['product.template'].search([('sale_ok', '=', True)])
products_count = len(products)

for count, product in enumerate(products):
    if not product.product_variant_ids:
        print(f"No variants for product template ID {product.id}. Skipping")
        continue
    product.list_price = min(variant.lst_price for variant in product.product_variant_ids)
    print(f"Processed product ID {product.id}")
    print(f"{products_count - count} out of {products_count} products remaining")

self._cr.commit()
