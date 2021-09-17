import json
import time

from tqdm import tqdm

# Change with correct path
RULES_FILE = "/Users/matteoserafini/sviluppo/mcom_odoo/netaddiction_addons/scripts/migration_rules.json"
DUPLICATES_FILE = "/Users/matteoserafini/sviluppo/mcom_odoo/netaddiction_addons/scripts/duplicates_attribute.json"

with open(RULES_FILE) as r:
    migrations = json.load(r)

with open(DUPLICATES_FILE) as d:
    duplicates_list = json.load(d)

ts = time.time()
for count, duplicate in enumerate(tqdm(duplicates_list)):
    product = self.env["product.product"].search([("id", "=", duplicate["product_id"])])
    if not product:
        continue
    for attribute in duplicate["duplicates"]:
        current_type = attribute["type"]
        current_attribute = attribute["name"]
        migrations_list = [m for m in migrations if m["type"] == current_type if m["attr_name"] == current_attribute]
        if not migrations_list:
            continue
        for migration in migrations_list:
            print(migration)
