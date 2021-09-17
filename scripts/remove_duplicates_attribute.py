# This script should be executed inside a NetAddiction Odoo 9 shell.

import json


def remove_duplicate_attributes(product):
    seen_ids = set()
    duplicate_list = []
    for attr in product.attribute_value_ids:
        if attr.attribute_id.id not in seen_ids:
            seen_ids.add(attr.attribute_id.id)
        else:
            duplicate_list.append(attr)
    if duplicate_list:
        product.write({"attribute_value_ids": [(3, attr.id) for attr in duplicate_list]})
        return duplicate_list


duplicates = []
products = self.env["product.product"].search([])
for count, product in enumerate(products):
    duplicate = remove_duplicate_attributes(product)
    if duplicate:
        print(duplicate)
        duplicates.append(
            {
                "product_id": product.id,
                "duplicates": [{"name": a.name, "type": a.attribute_id.display_name} for a in duplicate],
            }
        )
    if not count % 100:
        self._cr.commit()
self._cr.commit()

if duplicates:
    with open("duplicates_found.json", "w") as fp:
        json.dump(duplicates, fp, sort_keys=True, indent=4, separators=(",", ": "))