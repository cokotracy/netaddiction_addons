import requests
import time

from tqdm import tqdm


def get_old_urls(offset, max_per_page):
    r = requests.get(
        "http://staging2.multiplayer.com/api/product/",
        params={"offset": offset, "max_per_page": max_per_page},
        verify=False,
    )
    print(f"Current url: {r.url}")
    if r.status_code == requests.codes.ok:
        return r.json()


def set_redirect(urls):
    for count, url in enumerate(tqdm(urls)):
        if self.env["website.rewrite"].search([("url_from", "=", url["abs_url"])]):
            continue
        product = self.env["product.product"].search([("id", "=", url["odoo_id"]), ("active", "in", [True, False])])
        if not product:
            continue
        redirect = self.env["website.rewrite"].create(
            {
                "name": f"Redirect: {product.display_name}",
                "redirect_type": "301",
                "url_from": url["abs_url"],
                "url_rewrite": "custom_url",
                "url_to": product.website_url,
            }
        )
        # Commit on DB every 1000 redirect
        if not count % 1000:
            self._cr.commit()

    # Commit the remaining redirect
    self._cr.commit()


def migrate_from_api():
    print("Migrate from API")
    next_page = True
    offset = 0
    max_per_page = 10000
    while next_page:
        response = get_old_urls(offset, max_per_page)
        if response:
            set_redirect(response)
            offset += max_per_page
        else:
            next_page = False
            break


ts = time.time()
migrate_from_api()
print("Time:", time.time() - ts)
