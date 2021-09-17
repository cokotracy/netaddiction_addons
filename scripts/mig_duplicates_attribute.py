import json
import time
from datetime import date

from tqdm import tqdm

# Change with correct path
RULES_FILE = "/Users/matteoserafini/sviluppo/mcom_odoo/netaddiction_addons/scripts/migration_rules.json"
DUPLICATES_FILE = "/Users/matteoserafini/sviluppo/mcom_odoo/netaddiction_addons/scripts/duplicates_attribute.json"

with open(RULES_FILE) as r:
    migrations = json.load(r)

with open(DUPLICATES_FILE) as d:
    duplicates_list = json.load(d)


def get_or_create_tag(name):
    tag = self.env["product.template.tag"].search([("name", "=", name)])
    if not tag:
        print(f"Tag da creare: {name}")
        tag = self.env["product.template.tag"].create(
            {
                "name": name,
                "sequence": 10,
                "company_id": 1,
                "create_uid": 2,
                "write_uid": 2,
                "create_date": date.today(),
                "write_date": date.today(),
            }
        )
        print(f"Tag -> Creato: {tag.name}")
    return tag


def get_or_create_brand(name):
    brand = self.env["product.brand.ept"].search([("name", "=", name)])
    if not brand:
        print(f"Brand -> Da creare: {name}")
        brand = self.env["product.brand.ept"].create(
            {
                "name": name,
                "description": f"I migliori prodotti targati {name}",
                "is_published": True,
                "sequence": 10,
                "create_uid": 2,
                "write_uid": 2,
                "create_date": date.today(),
                "write_date": date.today(),
            }
        )
        print(f"Brand -> Creato: {brand.name}")
    return brand


def set_category(name, product):
    category = self.env["product.public.category"].search([("name", "=", name)])
    if not category:
        return
    if category.id not in product.public_categ_ids.ids:
        product.write({"public_categ_ids": [(4, category.id)]})
        print(f"Categoria -> Associata con il prodotto")
    return category.id


def set_tag(name, product):
    tag = get_or_create_tag(name)
    if not tag:
        print(f"Tag -> Errore per il brand: {name}")
    if tag.id not in product.tag_ids.ids:
        product.write({"tag_ids": [(4, tag.id)]})
        print(f"Tag -> Associato con il prodotto")


def set_brand(name, product):
    brand = get_or_create_brand(name)
    if not brand:
        print(f"Brand -> Errore per il brand: {name}")
    product.write({"product_brand_ept_id": brand.id})
    print(f"Brand -> Associato con il prodotto")


def check_condition(product_cat, conditions, attributes):
    for condition in conditions:
        if type(condition) is str:
            if condition in attributes:
                is_valid = True
            else:
                return False
        if type(condition) is list:
            if any(x in condition for x in attributes):
                is_valid = True
            else:
                return False
        if type(condition) is dict:
            if "category" in condition and condition["category"]:
                if product_cat.name in condition["category"]:
                    is_valid = True
                else:
                    return False
            if "exclude" in condition and condition["exclude"]:
                if product_cat.name in condition["exclude"]:
                    return False
    return is_valid


_error = {"tag": [], "category": [], "brand": []}

ts = time.time()
for count, duplicate in enumerate(tqdm(duplicates_list)):
    product = self.env["product.product"].search([("id", "=", duplicate["product_id"])])
    if not product:
        continue
    attribute_list = [a.name for a in product.product_template_attribute_value_ids]
    for attribute in duplicate["duplicates"]:
        current_type = attribute["type"]
        current_attribute = attribute["name"]
        migrations_list = [m for m in migrations if m["type"] == current_type if m["attr_name"] == current_attribute]
        if not migrations_list:
            continue
        for migration in migrations_list:
            if not migration["operations"]:
                continue
            for operation in migration["operations"]:
                if operation["conditions"]:
                    if not check_condition(product.categ_id, operation["conditions"], attribute_list):
                        continue
                if operation["new_type"] == "Tag":
                    try:
                        set_tag(operation["new_name"], product)
                    except Exception as e:
                        _error["tag"].append(f"{product.id}: {e}")
                if operation["new_type"] == "SottoCategoria":
                    try:
                        set_category(operation["new_name"], product)
                    except Exception as e:
                        _error["category"].append(f"{product.id}: {e}")
                if operation["new_type"] == "Brand":
                    if not product.product_brand_ept_id:
                        try:
                            set_brand(operation["new_name"], product)
                        except Exception as e:
                            _error["brand"].append(f"{product.id}: {e}")
        # Commit on DB every 100 products

    if not count % 100:
        self._cr.commit()

# Commit the remaining products
self._cr.commit()


with open("error_migration_duplicate.json", "w") as fp:
    json.dump(_error, fp, sort_keys=True, indent=4, separators=(",", ": "))

print("Time:", time.time() - ts)
