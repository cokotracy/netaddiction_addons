import json
import requests
import time

from tqdm import tqdm

# Change with correct path
URLS_FILE = "/Users/matteoserafini/sviluppo/mcom_odoo/netaddiction_addons/scripts/old_urls.json"

with open(URLS_FILE) as f:
    urls = json.load(f)

ts = time.time()

for url in tqdm(urls):
    product = self.env["product.product"].search([("id", "=", url["odoo_id"])])
    if not product:
        continue
    if self.env["website.rewrite"].search([("url_from", "=", url["old_url"])]):
        continue
    redirect = self.env["website.rewrite"].create(
        {
            "name": f"Redirect: {product.display_name}",
            "redirect_type": "301",
            "url_from": url["old_url"],
            "url_rewrite": "custom_url",
            "url_to": product.website_url,
        }
    )
    print("Redirect creato")
    self._cr.commit()