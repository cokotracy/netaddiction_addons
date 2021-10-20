import requests

from tqdm import tqdm


def get_user_token(page, social):
    url = f"http://staging2.multiplayer.com/api/user-token/?page={page}&social={social}"
    r = requests.get(url, verify=False)
    if r.status_code == requests.codes.ok:
        return r.json()


def create_user(users, social):
    for count, user in enumerate(tqdm(users)):
        res_user = self.env["res.users"].search([("partner_id", "=", user["odoo_id"])])
        if not res_user:
            continue
        args = {}
        args["oauth_access_token"] = ""
        args["oauth_uid"] = user["token"]
        if social == "google":
            args["oauth_provider_id"] = 3
        elif social == "facebook":
            args["oauth_provider_id"] = 2
        try:
            res_user.write(args)
        except Exception as e:
            pass

        # Commit on DB every 500 users
        if not count % 500:
            self._cr.commit()

    # Commit the remaining users
    self._cr.commit()


def migrate_token(social):
    next_page = True
    page = 1
    while next_page:
        print(f"Social:{social} | Retriving page: {page}")
        response = get_user_token(page, social)
        if response:
            next_page = True if "next" in response else False
            create_user(response.get("results", []), social)
            page += 1
        else:
            break


for s in ["google", "facebook"]:
    migrate_token(s)
