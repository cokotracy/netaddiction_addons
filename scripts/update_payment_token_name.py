import stripe
from tqdm import tqdm


def get_stripe_customer(partner):
    customer = stripe.Customer.list(email=partner.email)
    try:
        customer_id = customer.data[0]["id"]
    except IndexError:
        return
    return customer_id


def get_stripe_card(customer, card_token):
    try:
        card = stripe.Customer.retrieve_source(customer, card_token)
    except Exception as e:
        return
    return card


try:
    acquirer = self.env["payment.acquirer"].search(
        [("provider", "=", "netaddiction_stripe"), ("state", "=", "enabled")]
    )[0]
except IndexError:
    pass
else:
    stripe.api_key = acquirer.netaddiction_stripe_sk
    for count, token in enumerate(tqdm(self.env["payment.token"].search([]))):
        if token.netaddiction_stripe_payment_method:
            customer = get_stripe_customer(token.partner_id)
            if not customer:
                continue
            card = get_stripe_card(customer, token.netaddiction_stripe_payment_method)
            if not card:
                continue
            token.write({"name": f"XXXXXXXXXXXX{card.get('last4', '****')}"})

        # Commit on DB every 500 token
        if not count % 500:
            self._cr.commit()

    # Commit the remaining users
    self._cr.commit()
