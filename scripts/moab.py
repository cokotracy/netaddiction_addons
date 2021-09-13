# This script should be executed inside a NetAddiction Odoo 14 shell
# Attention! Install: pip install tqdm

import json
import requests
import time
from datetime import date

from tqdm import tqdm

# Change with correct path
RULES_FILE = "migration_rules.json"


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
        self._cr.commit()
        print(f"Tag -> Creato e salvato nel DB {tag.name}")
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
        self._cr.commit()
        print(f"Brand -> Creato e salvato nel DB {brand.name}")
    return brand


def set_category(name, product):
    category = self.env["product.public.category"].search([("name", "=", name)])
    if not category:
        return
    if category.id not in product.public_categ_ids.ids:
        product.write({"public_categ_ids": [(4, category.id)]})
        self._cr.commit()
        print(f"Categoria -> Associazione con il prodotto salvata nel DB")
    return category.id


def set_tag(name, product):
    tag = get_or_create_tag(name)
    if not tag:
        print(f"Tag -> Errore per il brand: {name}")
    if tag.id not in product.tag_ids.ids:
        product.write({"tag_ids": [(4, tag.id)]})
        self._cr.commit()
        print(f"Tag -> Associazione con il prodotto salvata nel DB")


def set_brand(name, product):
    brand = get_or_create_brand(name)
    if not brand:
        print(f"Brand -> Errore per il brand: {name}")
    product.write({"product_brand_ept_id": brand.id})
    self._cr.commit()
    print(f"Brand -> Associazione con il prodotto salvata nel DB")


def get_old_seo_url(product_id):
    r = requests.get("http://staging2.multiplayer.com/api/product/", params={"odoo_id": product_id}, verify=False)
    if r.status_code == requests.codes.ok:
        return r.text.replace('"', "")


def set_redirect(product):
    if self.env["website.rewrite"].search([("url_to", "=", product.website_url)]):
        return

    old_url = get_old_seo_url(product.id)
    if not old_url:
        return
    redirect = self.env["website.rewrite"].create(
        {
            "name": f"Redirect: {product.display_name}",
            "url_from": old_url,
            "url_rewrite": "custom_url",
            "url_to": product.website_url,
        }
    )
    self._cr.commit()


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


_error = {"rewrite": [], "tag": [], "category": [], "brand": []}


with open(RULES_FILE) as f:
    migrations = json.load(f)

ts = time.time()
products = self.env["product.product"].search([])[:100]
for product in tqdm(products):
    try:
        set_redirect(product)
    except Exception as e:
        _error["rewrite"].append(f"{product.id}: {e}")

    attribute_list = [a.name for a in product.product_template_attribute_value_ids]
    for attribute in product.product_template_attribute_value_ids:
        current_type = attribute.attribute_id.display_name
        current_attribute = attribute.name
        migrations_list = [m for m in migrations if m["type"] == current_type if m["attr_name"] == current_attribute]
        if not migrations_list:
            continue
        for migration in migrations_list:
            if not migration["operations"]:
                continue
            for operation in migration["operations"]:
                if operation["conditions"]:
                    if not check_condition(product.categ_id, operation["conditions"], attribute_list):
                        if product.id not in _error["conditions"]:
                            _error["conditions"].append(product.id)
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

with open("error_migration.json", "w") as fp:
    json.dump(_error, fp, sort_keys=True, indent=4, separators=(",", ": "))

print("Time:", time.time() - ts)
