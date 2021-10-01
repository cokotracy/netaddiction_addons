import json
import time

from tqdm import tqdm

# Change with correct path
URLS_FILE = "/opt/Rapsodoo/netaddiction_addons/scripts/old_urls.json"


def migrate_from_json():
    print(f"Migration from JSON")
    with open(URLS_FILE) as f:
        urls_file = json.load(f)

    for count, url in enumerate(tqdm(urls_file)):
        product = self.env["product.product"].search([("id", "=", url["odoo_id"])])
        if not product:
            continue
        if self.env["website.rewrite"].search([("url_from", "=", url["old_url"])]):
            continue
        redirect = self.env["website.rewrite"].create(
            {
                "name": f"Redirect: {product.display_name}",
                "redirect_type": "301",
                "url_from": f"/{url['old_url']}",
                "url_rewrite": "custom_url",
                "url_to": product.website_url,
            }
        )
        print("Redirect creato")

        # Commit on DB every 100 redirect
        if not count % 100:
            self._cr.commit()

    # Commit the remaining redirect
    self._cr.commit()


ts = time.time()
migrate_from_json()
print("Time:", time.time() - ts)
