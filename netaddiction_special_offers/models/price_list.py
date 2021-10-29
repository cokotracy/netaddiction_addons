from odoo import fields, models


class ProductPricelistDynamicDomain(models.Model):
    _inherit = "product.pricelist.dynamic.domain"

    # Web
    website_url = fields.Char(
        "Website URL", compute="_website_url", help="The full URL to access the document through the website."
    )
    description = fields.Char("Descrizione")
    desktop_image = fields.Image("Immagine Desktop")
    mobile_image = fields.Image("Immagine Mobile")
    active_frontend_filter = fields.Boolean(
        "Attivare i filtri?", default=True, help="Attiva la barra laterale dei filtri nella pagina frontend dela tag"
    )

    def open_website_url(self):
        return {
            "type": "ir.actions.act_url",
            "url": self.website_url,
            "target": "self",
        }

    def _website_url(self):
        for list_price in self:
            list_price.website_url = f"/offerte/{self.id}"
