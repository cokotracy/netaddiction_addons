import requests
import json


def get_users(page):
    url = f"http://staging2.multiplayer.com/api/user/?page={page}"
    r = requests.get(url, verify=False)
    if r.status_code == requests.codes.ok:
        return r.json()


def create_user(users):
    for user in users:
        if not user["email"]:
            continue
        if self.env["res.users"].search([("login", "=", user["email"])]):
            continue
        res_partner = self.env["res.partner"].search([("id", "=", user["odoo_id"])])
        if not res_partner:
            continue
        args = {
            "login": user["email"],
            "email": user["email"],
            "partner_id": res_partner.id,
            "groups_id": [(6, 0, [12])],
        }
        if user["first_name"] != "" and user["last_name"] != "":
            args["name"] = f"{user['first_name']} {user['last_name']}"
        else:
            args["name"] = user["email"]
        if user["google_token"]:
            args["oauth_access_token"] = user["google_token"]
            args["oauth_provider_id"] = 3
        elif user["facebook_token"]:
            args["oauth_access_token"] = user["facebook_token"]
            args["oauth_provider_id"] = 2
        try:
            user = self.env["res.users"].with_context(no_reset_password=True).create(args)
            print(f"User created: {user.email}")
            self._cr.commit()
        except Exception as e:
            global _error_log
            _error_log.append(f"{user['email']}: {e}")


_error_log = []
next_page = True
page = 1
while next_page:
    print(f"Retriving page: {page}")
    response = get_users(page)
    if response:
        next_page = True if "next" in response else False
        create_user(response.get("results", []))
        page += 1
    else:
        break

if _error_log:
    with open("error_user_migration.json", "w") as fp:
        json.dump(_error_log, fp, sort_keys=True, indent=4, separators=(",", ": "))
